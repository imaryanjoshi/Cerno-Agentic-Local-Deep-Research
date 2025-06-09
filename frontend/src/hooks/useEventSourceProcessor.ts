// src/hooks/useEventSourceProcessor.ts
import React, {useCallback, useRef} from 'react';
import type {AgentAction, AgentMessageData, MessageData, Session, TaskStepData} from '../types';

interface UseEventSourceProcessorProps {
    setMessages: React.Dispatch<React.SetStateAction<MessageData[]>>;
    setSessions: React.Dispatch<React.SetStateAction<Session[]>>;
    setArtifacts: React.Dispatch<React.SetStateAction<any[]>>;
    setIsTaskRunning: (isRunning: boolean) => void;
    onStepCompleted: (completedStepIndex: number) => void;
    onTaskCompleted?: (status: 'success' | 'error') => void; // CHANGED FROM onStepCompleted
}

export const useEventSourceProcessor = ({
                                            setIsTaskRunning,
                                            setMessages,
                                            setSessions,
                                            setArtifacts, // Keep this if you use it, otherwise it can be removed too
                                            onTaskCompleted,
                                            onStepCompleted
                                        }: UseEventSourceProcessorProps) => {
    const eventSourceRef = useRef<EventSource | null>(null);
    const currentAgentMessageIdRef = useRef<string | null>(null);
    const accumulatedLLMTokensRef = useRef<{ [stepIndex: number]: string }>({});
    const inactivityTimeoutRef = useRef<NodeJS.Timeout | null>(null);

    const onStreamEnd = useCallback(() => {
        console.log("SSE stream ended by server 'stream_end' event.");
        setMessages(prevMessages => {
            const currentAgentMsgId = currentAgentMessageIdRef.current;
            if (!currentAgentMsgId) return prevMessages;
            const msgIndex = prevMessages.findIndex(msg => msg.id === currentAgentMsgId);
            if (msgIndex === -1) return prevMessages;

            const newMessages = [...prevMessages];
            const agentMessage = { ...newMessages[msgIndex] } as AgentMessageData;

            // FINAL CHECK: If the task is still in a 'loader' state when the stream
            // officially ends, it means something went wrong or it ended prematurely.
            if (agentMessage.task && agentMessage.task.statusIcon === 'loader') {
                agentMessage.task.statusIcon = 'error';
                agentMessage.task.title = "Task ended unexpectedly.";
                const activeStepIndex = agentMessage.task.currentStepIndex;
                if (activeStepIndex !== undefined && activeStepIndex >= 0 && agentMessage.task.steps[activeStepIndex]) {
                    agentMessage.task.steps[activeStepIndex].status = 'error';
                }
                // If the task failed here, trigger the completion callback
                if (onTaskCompleted) onTaskCompleted('error');
            }
            newMessages[msgIndex] = agentMessage;
            return newMessages;
        });
        // Call cleanup from within, but don't pass cleanup to its own dependency array
        if (eventSourceRef.current) {
            eventSourceRef.current.close();
            eventSourceRef.current = null;
        }
    }, [setMessages]); // Depends only on setMessages

    const cleanupEventSource = useCallback((reason?: string) => {
        console.log(`Closing EventSource. Reason: ${reason}`);
        // Clear any existing timeout when we clean up
        if (inactivityTimeoutRef.current) {
            clearTimeout(inactivityTimeoutRef.current);
            inactivityTimeoutRef.current = null;
        }
        if (eventSourceRef.current) {
            eventSourceRef.current.close();
            eventSourceRef.current = null;
        }
        currentAgentMessageIdRef.current = null;
        setIsTaskRunning(false);
    }, [setIsTaskRunning]);
    const resetInactivityTimeout = useCallback(() => {
        if (inactivityTimeoutRef.current) {
            clearTimeout(inactivityTimeoutRef.current);
        }

        inactivityTimeoutRef.current = setTimeout(() => {
            console.warn("SSE Inactivity Timeout: No message received. Assuming connection is lost.");

            setMessages(prevMessages => {
                const currentAgentMsgId = currentAgentMessageIdRef.current;
                if (!currentAgentMsgId) return prevMessages;
                const msgIndex = prevMessages.findIndex(msg => msg.id === currentAgentMsgId);
                if (msgIndex === -1) return prevMessages;

                const newMessages = [...prevMessages];
                const failedMessage = { ...newMessages[msgIndex] } as AgentMessageData;

                if (failedMessage.task && failedMessage.task.statusIcon === 'loader') {
                    failedMessage.task.statusIcon = 'error';
                    failedMessage.task.title = "Task timed out or connection lost.";
                    const activeStepIndex = failedMessage.task.currentStepIndex;
                    if (activeStepIndex !== undefined && activeStepIndex >= 0 && failedMessage.task.steps[activeStepIndex]) {
                        failedMessage.task.steps[activeStepIndex].status = 'error';
                    }
                }
                newMessages[msgIndex] = failedMessage;
                return newMessages;
            });

            cleanupEventSource("Inactivity timeout");
        }, 30000); // 30 seconds. Adjust as needed.
    }, [cleanupEventSource, setMessages]);

    const startStream = useCallback((userInput: string, agentMessageId: string, modelId: string, sessionId: string) => {
        setIsTaskRunning(true)
        currentAgentMessageIdRef.current = agentMessageId;

        setMessages(prevMessages => {
            const existingMsgIndex = prevMessages.findIndex(msg => msg.id === agentMessageId);
            if (existingMsgIndex > -1) {
                const updatedMsg = {
                    ...(prevMessages[existingMsgIndex] as AgentMessageData),
                    task: {
                        title: `Starting Research: ${userInput.substring(0, 50)}${userInput.length > 50 ? '...' : ''}`,
                        statusIcon: 'loader' as const,
                        steps: [],
                        totalSteps: 0,
                        currentStepIndex: -1,
                    }
                };
                const newMessages = [...prevMessages];
                newMessages[existingMsgIndex] = updatedMsg;
                return newMessages;
            }
            return prevMessages;
        });


        const es = new EventSource(`/api/prompt/?prompt=${encodeURIComponent(userInput)}&model_id=${encodeURIComponent(modelId)}&session_id=${encodeURIComponent(sessionId)}`);
        console.log(`[EventSource] Connecting`);

        eventSourceRef.current = es;
        resetInactivityTimeout();

        es.onopen = () => {
            console.log("[EventSource] Connection opened successfully.");
        };
        es.onmessage = (event) => {
            resetInactivityTimeout();
            if (!event.data) return;

            try {
                const parsedData = JSON.parse(event.data);

                if (parsedData.type === 'session_done') {
                    // Treat this as the definitive end, similar to 'stream_end'
                    onStreamEnd();
                    return;
                }
                console.log(`[EventSource] Processing event type: ${parsedData.type} and updating state...`);

                setMessages(prevMessages => {
                    const currentAgentMsgId = currentAgentMessageIdRef.current;
                    if (!currentAgentMsgId) return prevMessages;
                    const msgIndex = prevMessages.findIndex(msg => msg.id === currentAgentMsgId);
                    if (msgIndex === -1) return prevMessages;

                    const agentMessage = { ...prevMessages[msgIndex] } as AgentMessageData;
                    if (!agentMessage.task) {
                        agentMessage.task = { title: userInput.substring(0,50) + "...", steps: [], totalSteps: 0, currentStepIndex: -1, statusIcon: 'loader' };
                    }
                    const task = { ...agentMessage.task };
                    const steps = [...task.steps];

                    switch (parsedData.type) {
                        case 'plan_ready':
                            task.totalSteps = parsedData.task_count;
                            break;

                        case 'step_started':
                            const startedStepIndex = parsedData.step_index;
                            // Dynamically grow the steps array if needed
                            if (startedStepIndex >= steps.length) {
                                while (steps.length <= startedStepIndex) {
                                    steps.push({ id: `step_${steps.length}`, description: "Pending...", status: 'pending' });
                                }
                            }
                            // Update the specific step
                            steps[startedStepIndex] = {
                                ...steps[startedStepIndex],
                                description: parsedData.description,
                                status: 'running',
                                isActive: true,
                                agentId: parsedData.agent_id,
                            };
                            task.currentStepIndex = startedStepIndex;
                            // Mark previous steps as not active
                            for (let i = 0; i < startedStepIndex; i++) {
                                if (steps[i]) steps[i].isActive = false;
                            }
                            break;

                        case 'step_call_name_announcement':
                            const announcementStepIndex = parsedData.step_index;
                            if (announcementStepIndex < steps.length && steps[announcementStepIndex]) {
                                steps[announcementStepIndex].description = parsedData.description;
                                steps[announcementStepIndex].callName = parsedData.call_name;
                                steps[announcementStepIndex].isActive = true;
                                task.currentStepIndex = announcementStepIndex;
                            }
                            break

                        case 'step_agent_activity':
                            const activityStepIndex = parsedData.step_index;
                            if (activityStepIndex < steps.length && steps[activityStepIndex]) {
                                const currentStep = { ...steps[activityStepIndex] };
                                if (!currentStep.agentActions) currentStep.agentActions = [];

                                if (parsedData.event === 'ToolCallStarted') {
                                    const toolCallData = parsedData.data;
                                    let newAction: AgentAction;

                                    if (toolCallData.tool_name === 'atransfer_task_to_member') {
                                        const args: { [key: string]: string } = {};
                                        toolCallData.args_str.split(', ').forEach((arg: string) => {
                                            const [key, ...valueParts] = arg.split('=');
                                            if (key) args[key.trim()] = valueParts.join('=').trim();
                                        });

                                        newAction = {
                                            id: `delegated_${args.member_id || 'unknown'}_${Date.now()}`,
                                            type: 'delegated_task',
                                            // CHANGE THIS LINE: Just the agent name is the prefix now
                                            prefix: args.member_id || 'Sub-agent',
                                            detail: args.task_description || "Performing sub-task...",
                                            status: 'running',
                                            originalToolName: toolCallData.tool_name,
                                            memberAgentId: args.member_id,
                                        };
                                    } else {
                                        // This part for other tools remains the same
                                        newAction = {
                                            id: `${toolCallData.tool_name}_${Date.now()}`,
                                            type: 'tool_call',
                                            prefix: `Tool: ${toolCallData.tool_name}`,
                                            detail: `Args: ${toolCallData.args_str.substring(0,100)}...`,
                                            status: 'running',
                                        };
                                    }
                                    currentStep.agentActions = [...currentStep.agentActions, newAction];
                                }
                                else if (parsedData.event === 'ToolCallCompleted') {
                                    const toolData = parsedData.data;
                                    currentStep.agentActions = currentStep.agentActions.map(action => {
                                        if (action.status === 'running') {
                                            if (toolData.tool_name === 'atransfer_task_to_member' && action.type === 'delegated_task' && action.originalToolName === toolData.tool_name) {
                                                return { ...action, status: 'success' };
                                            } else if (action.type === 'tool_call' && action.prefix.includes(toolData.tool_name)) {
                                                return { ...action, status: 'success' };
                                            }
                                        }
                                        return action;
                                    });
                                } else if (parsedData.event === 'LLMToken') {

                                }
                                steps[activityStepIndex] = currentStep;
                            }
                            break;

                        case 'step_completed':
                            const completedStepIndex = parsedData.step_index;
                            if (completedStepIndex < steps.length && steps[completedStepIndex]) {
                                // 1. Update the specific step's status from the event data
                                steps[completedStepIndex].status = parsedData.status as 'success' | 'error';
                                steps[completedStepIndex].isActive = false;

                                // 2. Check if the ENTIRE task is now complete
                                const completedStepsCount = steps.filter(s => s.status === 'success' || s.status === 'error').length;
                                const isTaskComplete = task.totalSteps > 0 && completedStepsCount === task.totalSteps;

                                if (isTaskComplete) {
                                    const hasError = steps.some(step => step.status === 'error');
                                    const finalStatus = hasError ? 'error' : 'success';
                                    // Only set the final checkmark/error icon when the whole task is done
                                    task.statusIcon = finalStatus === 'success' ? 'check' : 'error';
                                    if (onTaskCompleted) {
                                        onTaskCompleted(finalStatus);
                                    }
                                } else if (parsedData.status === 'error') {
                                    // If an individual step fails, mark the whole task as failed immediately
                                    task.statusIcon = 'error';
                                    if (onTaskCompleted) {
                                        onTaskCompleted('error');
                                    }
                                }
                                // Otherwise, the task statusIcon remains 'loader'
                            }
                            // Call the onStepCompleted callback regardless, to trigger file refresh etc.
                            if (onStepCompleted) {
                                onStepCompleted(completedStepIndex);
                            }
                            break;

                        default:
                    }

                    agentMessage.task = task;
                    agentMessage.task.steps = steps;
                    const newMessages = [...prevMessages];
                    newMessages[msgIndex] = agentMessage;
                    return newMessages;
                });
            } catch (e) {
                console.error("Failed to parse SSE event data:", event.data, e);
            }
        };

        es.onerror = (err) => {

            console.error("EventSource connection failed:", err);

            // Immediately close the source to prevent any further events or retries
            cleanupEventSource("Connection error");

            // Now, safely update the UI state
            setMessages(prevMessages => {
                const currentAgentMsgId = currentAgentMessageIdRef.current;
                // Even if currentAgentMsgId was cleared, we can find the last agent message
                const lastAgentMsgIndex = prevMessages.slice().reverse().findIndex(m => m.sender === 'agent');
                if (lastAgentMsgIndex === -1) return prevMessages;

                const msgIndex = prevMessages.length - 1 - lastAgentMsgIndex;
                const newMessages = [...prevMessages];
                const failedMessage = { ...newMessages[msgIndex] } as AgentMessageData;

                if (failedMessage.task) {
                    failedMessage.task.statusIcon = 'error';
                    failedMessage.task.title = "Connection to agent lost";
                    const activeStepIndex = failedMessage.task.currentStepIndex;
                    if (activeStepIndex !== undefined && activeStepIndex >= 0 && failedMessage.task.steps[activeStepIndex]) {
                        failedMessage.task.steps[activeStepIndex].status = 'error';
                        failedMessage.task.steps[activeStepIndex].isActive = false;
                    }
                } else {
                    failedMessage.text = "An error occurred: Connection lost.";
                }
                newMessages[msgIndex] = failedMessage;
                return newMessages;
            });
        };

        es.addEventListener('stream_end', (event) => {
            // <<< LOGGING >>>
            console.log("[EventSource] 'stream_end' event received.", event);
            onStreamEnd();
        });

    }, [setIsTaskRunning,setMessages, resetInactivityTimeout, onStreamEnd, onStepCompleted, onTaskCompleted, cleanupEventSource]);
    const stopStream = useCallback(async (sessionId: string) => {
        if (!sessionId) return;

        console.log("Requesting to stop task for session:", sessionId);

        // --- THE FIX IS HERE ---
        // Immediately update the UI to show a "stopped" state
        setMessages(prevMessages => {
            return prevMessages.map(msg => {
                if (msg.sender === 'agent' && msg.task && msg.task.statusIcon === 'loader') {
                    const updatedTask = { ...msg.task };
                    updatedTask.statusIcon = 'error'; // Show an error on the main task
                    updatedTask.title = "Task stopped by user.";

                    const activeStepIndex = updatedTask.currentStepIndex;
                    if (activeStepIndex !== undefined && activeStepIndex >= 0 && updatedTask.steps[activeStepIndex]) {
                        // Mark the currently running step as 'stopped'
                        const newSteps = [...updatedTask.steps];
                        newSteps[activeStepIndex] = {
                            ...newSteps[activeStepIndex],
                            status: 'stopped', // The new status
                            isActive: false,
                        };
                        updatedTask.steps = newSteps;
                    }
                    return { ...msg, task: updatedTask };
                }
                return msg;
            });
        });

        cleanupEventSource("User requested stop");

        try {
            await fetch('/api/agent/stop/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ session_id: sessionId }),
            });
        } catch (error) {
            console.error("Error sending stop signal to backend:", error);
        }
    }, [cleanupEventSource,setMessages]);
    return { startStream,stopStream, cleanupEventSource };
};