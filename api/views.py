import asyncio
import json
import logging
import mimetypes
import os
import re
import threading

from agno.exceptions import ModelProviderError
from django.http import StreamingHttpResponse, JsonResponse, HttpResponseBadRequest, HttpResponseNotFound, FileResponse, \
    HttpResponse, Http404
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from api.agents.initial_response_and_planner_agent import get_planner_agent
from api.agents.step_executor import get_step_executor_team
from api.config import AGENT_OUTPUT_DIR  
from api.utils import update_markdown_plan_checkbox_by_description
from core import settings
from .llm_registry import get_llm_instance, get_available_models_grouped
from .serializers import PromptRequestSerializer

logger = logging.getLogger(__name__)
RUNNING_ASYNC_TASKS = {}

TASKS_LOCK = threading.Lock()
MODEL_PRICING = {
    
    "gpt-4o": {"input": 0.005 / 1000, "output": 0.015 / 1000},
    "gpt-4-turbo-preview": {"input": 0.01 / 1000, "output": 0.03 / 1000},
    "gpt-3.5-turbo-0125": {"input": 0.0005 / 1000, "output": 0.0015 / 1000},
    "gemini-2.0-flash-001": {"input": 0.000125 / 1000, "output": 0.000125 / 1000},
    "gpt-4.1-mini": {"input": 0.00015 / 1000, "output": 0.0016 / 1000},
    "gemini-2.5-flash-preview-05-20": {"input": 0.0004 / 1000, "output": 0.0006 / 1000},
    
}
@method_decorator(csrf_exempt, name='dispatch')
class StopAgentView(View):
    async def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            session_id = data.get('session_id')
            if not session_id:
                return JsonResponse({'error': 'session_id is required'}, status=400)

            logger.info(f"Received stop request for session_id: {session_id}")

            task_to_cancel = RUNNING_ASYNC_TASKS.get(session_id)

            if task_to_cancel and not task_to_cancel.done():
                
                task_to_cancel.cancel()
                logger.info(f"Cancellation requested for task corresponding to session {session_id}.")
                return JsonResponse({'status': 'cancellation signal sent'}, status=200)
            else:
                logger.warning(f"No active task found for session_id: {session_id} to stop.")
                return JsonResponse({'error': 'No running task found for this session'}, status=404)

        except Exception as e:
            logger.error(f"Error in StopAgentView: {e}", exc_info=True)
            return JsonResponse({'error': str(e)}, status=500)

def parse_agno_tool_call_data(chunk) -> dict | None:
    tool_name = None
    args_str = None  
    raw_info_for_fallback_parsing = None

    if hasattr(chunk, 'tool_calls') and chunk.tool_calls and isinstance(chunk.tool_calls, list):
        
        call_data = chunk.tool_calls[0]  
        if isinstance(call_data, dict):
            tool_name = call_data.get("name")
            arguments_raw = call_data.get("arguments")  
            if isinstance(arguments_raw, str):
                args_str = arguments_raw
            elif isinstance(arguments_raw, dict):  
                args_str = json.dumps(arguments_raw)
            else:
                args_str = str(arguments_raw)  
            logger.debug(f"Parsed from chunk.tool_calls: name={tool_name}, args_str={args_str}")
            return {"tool_name": tool_name, "args_str": args_str}
        else:  
            raw_info_for_fallback_parsing = str(chunk.tool_calls[0]) if chunk.tool_calls else ""

    elif hasattr(chunk, 'formatted_tool_calls'):
        
        temp_data = chunk.formatted_tool_calls
        if isinstance(temp_data, list):
            raw_info_for_fallback_parsing = temp_data[0] if temp_data else ""
        elif isinstance(temp_data, str):
            raw_info_for_fallback_parsing = temp_data
        else:  
            raw_info_for_fallback_parsing = str(temp_data)

    if isinstance(raw_info_for_fallback_parsing, str) and raw_info_for_fallback_parsing:
        
        match = re.match(r"([\w.-]+)\s*\((.*)\)\s*$", raw_info_for_fallback_parsing.strip())
        if match:
            tool_name = match.group(1)
            args_str = match.group(2)  
            logger.debug(
                f"Parsed via regex from '{raw_info_for_fallback_parsing}': name={tool_name}, args_str={args_str}")
            return {"tool_name": tool_name, "args_str": args_str}
        else:
            logger.warning(f"Regex did not match on tool call string: {raw_info_for_fallback_parsing}")
            return {"raw": raw_info_for_fallback_parsing}  

    logger.warning(f"Could not parse tool call information from chunk: {vars(chunk)}")
    return None  
@method_decorator(csrf_exempt, name='dispatch')
class PromptAPIViewAsync(View):
    async def _call_agent_for_final_json(self, agent_instance, payload_dict: dict) -> tuple[dict | None, dict | None]:
        
        full_response_str = ""
        parsed_json = None
        agent_metrics_dict = None
        try:
            async_iterator = await agent_instance.arun(json.dumps(payload_dict), stream=True, stream_intermediate_steps=False)
            async for chunk in async_iterator:
                if chunk and hasattr(chunk, 'content') and chunk.content:
                    full_response_str += chunk.content
            if not full_response_str:
                logger.error(f"Agent {agent_instance.name} returned empty response string for payload: {payload_dict}")
                return {"error_message": f"Agent {agent_instance.name} returned no response.", "plan_files_created": False}, None
            logger.info(f"Agent {agent_instance.name} raw full accumulated response: {full_response_str}")
            try:
                parsed_json = json.loads(full_response_str)
                logger.info(f"Successfully parsed entire response as JSON from {agent_instance.name}")
            except json.JSONDecodeError:
                logger.warning(f"Could not parse entire response as JSON from {agent_instance.name}. Attempting heuristic. Full: {full_response_str[:500]}")
                last_brace_index = full_response_str.rfind('}')
                if last_brace_index != -1:
                    current_search_index = last_brace_index
                    while current_search_index >= 0:
                        first_brace_index = full_response_str.rfind('{', 0, current_search_index + 1)
                        if first_brace_index != -1:
                            candidate_str = full_response_str[first_brace_index: last_brace_index + 1]
                            try:
                                parsed_json = json.loads(candidate_str)
                                logger.info(f"Successfully parsed JSON from suffix using heuristic: {candidate_str}")
                                break
                            except json.JSONDecodeError:
                                current_search_index = first_brace_index - 1
                                continue
                        else:
                            break
                if parsed_json is None:
                    logger.error(f"Could not extract JSON from response from {agent_instance.name} using heuristic. Full: {full_response_str}")
                    return {"error_message": f"Agent {agent_instance.name} output did not contain valid JSON.", "plan_files_created": False}, None
            if parsed_json and agent_instance.run_response and agent_instance.run_response.metrics:
                raw_metrics = agent_instance.run_response.metrics
                agent_metrics_dict = {"input_tokens": sum(raw_metrics.get('input_tokens', [0])), "output_tokens": sum(raw_metrics.get('output_tokens', [0])), "time": sum(raw_metrics.get('time', [0.0]))}
            return parsed_json, agent_metrics_dict
        except Exception as e:
            logger.exception(f"Critical error in _call_agent_for_final_json for {agent_instance.name}: {e}")
            return {"error_message": f"Critical error with agent {agent_instance.name}: {str(e)}", "plan_files_created": False}, None

    async def _stream_response_sse(self, user_prompt: str, model_id: str, session_id: str):
        def format_sse(data_dict: dict) -> bytes:
            return f"data: {json.dumps(data_dict)}\n\n".encode('utf-8')

        all_llm_call_details = []
        try:
            
            all_models_grouped = get_available_models_grouped()
            provider = next((p for p, models in all_models_grouped.items() if any(m['id'] == model_id for m in models)),
                            None)

            if not provider:
                logger.error(f"Orchestrator: Could not find provider for model_id: {model_id}")
                yield format_sse({"type": "error", "message": f"Model '{model_id}' is not currently available."})
                raise StopAsyncIteration

            llm = get_llm_instance(model_id=model_id, provider=provider)
            if not llm:
                logger.error(f"Orchestrator: Failed to create LLM instance for model '{model_id}'. Check API keys.")
                yield format_sse({"type": "error", "message": f"Could not initialize model '{model_id}'."})
                raise StopAsyncIteration

            planner_agent = get_planner_agent(llm)
            step_executor_team = get_step_executor_team(llm)

            yield format_sse({"type": "step_started", "step_index": 0, "description": "Making a plan...",
                              "agent_id": "PlannerAgent"})
            yield format_sse({"type": "step_call_name_announcement", "step_index": 0, "call_name": "generate_plan",
                              "description": "Making a plan..."})
            logger.info(f"SSE LOGIC [session: {session_id}]: Calling Planner agent...")

            planner_payload = {"user_prompt": user_prompt, "task": "generate_initial_response_and_plan"}
            planner_json_result, planner_run_metrics = await self._call_agent_for_final_json(planner_agent,
                                                                                             planner_payload)

            if planner_run_metrics:
                all_llm_call_details.append(
                    {"agent_name": planner_agent.name, "model_id": planner_agent.model.id, **planner_run_metrics})

            if not planner_json_result or planner_json_result.get("error_message"):
                error_msg = planner_json_result.get("error_message", "Planner agent failed to create plan files.")
                yield format_sse({"type": "step_completed", "step_index": 0, "status": "failed"})
                yield format_sse({"type": "error", "message": error_msg})
                raise StopAsyncIteration

            yield format_sse({"type": "step_completed", "step_index": 0, "status": "success"})
            yield format_sse({"type": "initial_ack", "content": planner_json_result.get("acknowledgment_message",
                                                                                        "Plan created. Starting execution...")})

            markdown_plan_filename = planner_json_result.get("markdown_plan_filename", "master_plan.md")
            json_plan_filename = planner_json_result.get("json_plan_filename", "master_plan.json")
            json_plan_path = os.path.join(AGENT_OUTPUT_DIR, json_plan_filename)

            try:
                with open(json_plan_path, "r", encoding="utf-8") as f:
                    plan_tasks_list = json.load(f)
                if not isinstance(plan_tasks_list, list): raise ValueError("Plan is not a list.")
                total_steps = 1 + len(plan_tasks_list)
                yield format_sse({"type": "plan_ready", "task_count": total_steps})
                logger.info(f"Orchestrator: Loaded {len(plan_tasks_list)} tasks from {json_plan_path}")
            except Exception as e:
                logger.error(f"Orchestrator: Failed to read/parse {json_plan_path}: {e}")
                yield format_sse({"type": "error", "message": f"Error reading plan: {e}"})
                raise StopAsyncIteration

            all_steps_succeeded = True
            for task_index, task_details_dict in enumerate(plan_tasks_list):
                task_agent_id = task_details_dict.get("agent_id")
                real_step_index = task_index + 1
                task_description = task_details_dict.get("description", "Unnamed Task")

                yield format_sse(
                    {"type": "step_started", "step_index": real_step_index, "description": task_description,
                     "agent_id": task_details_dict.get("agent_id")})
                yield format_sse({"type": "step_call_name_announcement", "step_index": real_step_index,
                                  "call_name": task_details_dict.get("call_name", "unknown_action"),
                                  "description": task_description})
                logger.info(f"Orchestrator: Starting task {real_step_index + 1}/{total_steps}: {task_description}")

                step_executor_final_text_output = ""
                step_success = False
                logger.info(f"SSE LOGIC [session: {session_id}]: Starting step {task_index}: {task_description}")
                try:
                    async_iterator_for_step = await step_executor_team.arun(json.dumps(task_details_dict), stream=True,
                                                                            stream_intermediate_steps=True)
                    async for chunk in async_iterator_for_step:
                        sse_payload_data = None
                        agno_event_type = getattr(chunk, 'event', None)
                        chunk_content = getattr(chunk, 'content', None)

                        if agno_event_type == 'RunResponse':
                            if chunk_content:
                                if chunk_content.startswith("E2B_STDOUT:"):
                                    e2b_data = chunk_content.replace("E2B_STDOUT:", "", 1).strip()
                                    sse_payload_data = {"event": "E2BTerminalOutput", "stream_type": "stdout",
                                                        "data": e2b_data}
                                elif chunk_content.startswith("E2B_STDERR:"):
                                    e2b_data = chunk_content.replace("E2B_STDERR:", "", 1).strip()
                                    sse_payload_data = {"event": "E2BTerminalOutput", "stream_type": "stderr",
                                                        "data": e2b_data}
                                else:
                                    step_executor_final_text_output += chunk_content
                                    sse_payload_data = {"event": "LLMToken", "data": chunk_content}

                        elif agno_event_type == 'RunCompleted':
                            if chunk_content:
                                step_executor_final_text_output = chunk_content
                            logger.info(
                                f"StepExecutor 'RunCompleted' for task '{task_description}'. Final message snippet: {step_executor_final_text_output[:100]}")

                        elif agno_event_type == 'ToolCallStarted':
                            tool_info = parse_agno_tool_call_data(chunk)
                            sse_payload_data = {"event": "ToolCallStarted", "data": tool_info}

                        elif agno_event_type == 'ToolCallCompleted':
                            tool_info = parse_agno_tool_call_data(chunk)
                            sse_payload_data = {"event": "ToolCallCompleted", "data": tool_info,
                                                "result_preview": str(chunk_content)[
                                                                  :200] if chunk_content else None}
                            if tool_info and tool_info.get(
                                    "tool_name") == "run_python_code" and task_agent_id == "E2BCodeExecutionAgent":
                                logger.info(
                                    f"E2B Script Output (via PythonTools for StepExecutor): {chunk_content}")

                        elif chunk_content and agno_event_type:
                            sse_payload_data = {"event": agno_event_type, "data": chunk_content}

                        if sse_payload_data:
                            yield format_sse({"type": "step_agent_activity", "step_index": real_step_index, **sse_payload_data})
                        await asyncio.sleep(0.001)

                    if step_executor_team.run_response and step_executor_team.run_response.metrics:  
                        raw_metrics = step_executor_team.run_response.metrics
                        all_llm_call_details.append({
                            "agent_name": f"{step_executor_team.name}_leader_step_{task_index}",
                            "model_id": step_executor_team.model.id,
                            "input_tokens": sum(raw_metrics.get('input_tokens', [0])),
                            "output_tokens": sum(raw_metrics.get('output_tokens', [0])),
                            "time": sum(raw_metrics.get('time', [0.0])),
                        })

                    if step_executor_final_text_output:
                        normalized_output = step_executor_final_text_output.strip().upper()
                        if "TASK_STEP_COMPLETED:" in normalized_output:
                            step_success = True
                        else:
                            step_success = False
                            logger.warning(
                                f"Orchestrator: StepExecutor for '{task_description}' output LACKED 'TASK_STEP_COMPLETED:' status line.")
                    else:
                        step_success = True
                        logger.warning(
                            f"Orchestrator: No final textual output from StepExecutor for '{task_description}'.")
                    step_success = True
                except ModelProviderError as e:
                    
                    logger.error(
                        f"A ModelProviderError occurred while processing the agent stream. This is often due to malformed JSON from the LLM.",
                        exc_info=True 
                    )
                    logger.error(f"The input that likely caused the error was: {json.dumps(task_details_dict, indent=2)}")
                    
                    error_payload = {
                        "type": "error",
                        "step_index": task_index,
                        "event": "FatalError",
                        "data": {
                            "message": "The AI model returned an invalid response. This can be a temporary issue. Please try again.",
                            "details": str(e)
                        }
                    }
                    yield format_sse(error_payload)
                except Exception as e:
                    logger.exception(
                        f"Orchestrator: Exception during StepExecutor call for task '{task_description}'")
                    step_success = False
                    yield format_sse(
                        {"type": "step_error", "step_index": task_index, "description": task_description,
                         "error_message": str(e)})

                update_markdown_plan_checkbox_by_description(markdown_plan_filename, task_description, step_success)
                yield format_sse({"type": "step_completed", "step_index": real_step_index,
                                  "status": "success" if step_success else "failed"})
                logger.info(f"Orchestrator: Completed task {task_index + 1}. Success: {step_success}")

                if not step_success:
                    all_steps_succeeded = False
                    logger.error(f"Orchestrator: Stopping due to failure in step: {task_description}")
                    yield format_sse(
                        {"type": "error", "message": f"Process stopped due to failure in step: {task_description}"})
                    break

            if all_steps_succeeded:
                logger.info("Orchestrator: All plan steps processed successfully. Preparing final summary.")
                final_deliverables = []
                for task_obj_final in plan_tasks_list:
                    if task_obj_final.get("outputs"):
                        for output_file_final in task_obj_final.get("outputs"):
                            output_path = os.path.join(AGENT_OUTPUT_DIR, output_file_final)
                            if os.path.exists(output_path):  
                                final_deliverables.append(
                                    {"filename": output_file_final, "path_in_workspace": output_file_final})
                            else:
                                logger.warning(
                                    f"Orchestrator: Planned output file '{output_file_final}' not found in workspace for final summary.")

                final_summary_payload = {
                    "type": "final_summary",
                    "summary_text": "The requested task has been processed successfully. Please find the generated artifacts listed below.",
                    "artifacts": final_deliverables
                }
                yield format_sse(final_summary_payload)
                logger.info(f"Orchestrator: Final summary sent with artifacts: {final_deliverables}")

        except StopAsyncIteration:
            logger.info("Orchestrator: SSE stream generation stopped by StopAsyncIteration.")
        except Exception as e:
            logger.exception("Orchestrator: Critical error in main orchestration flow.")
            try:
                yield format_sse({"type": "error", "message": f"Critical orchestration error: {e}"})
            except Exception:
                pass
        finally:
            total_cost = 0.0
            total_input_tokens = 0
            total_output_tokens = 0
            logger.info("--- AGENT RUN COST CALCULATION ---")
            for call_detail in all_llm_call_details:
                model_id = call_detail.get("model_id", "unknown_model")
                
                pricing_info = MODEL_PRICING.get(model_id)

                input_t = call_detail.get("input_tokens", 0)
                output_t = call_detail.get("output_tokens", 0)
                total_input_tokens += input_t
                total_output_tokens += output_t

                if pricing_info:
                    call_cost = (input_t * pricing_info["input"]) + (output_t * pricing_info["output"])
                    total_cost += call_cost
                    logger.info(
                        f"Agent: {call_detail['agent_name']}, Model: {model_id}, "
                        f"Input: {input_t}, Output: {output_t}, Time: {call_detail.get('time', 0):.2f}s, Cost: ${call_cost:.6f}"
                    )
                else:
                    logger.warning(
                        f"Pricing info not found for model: {model_id}. Call from {call_detail['agent_name']} not costed.")

            logger.info(
                f"TOTALS: Input Tokens: {total_input_tokens}, Output Tokens: {total_output_tokens}, Estimated Cost: ${total_cost:.6f}")

            yield format_sse({"type": "cost_summary", "total_input_tokens": total_input_tokens,
                              "total_output_tokens": total_output_tokens, "estimated_cost_usd": total_cost})
            yield format_sse({"type": "session_done"})
            logger.info("Orchestrator: Session done. SSE stream finished.")

    async def stream_wrapper(self, request, user_prompt, model_id, session_id):
        """
        Wraps the SSE generator in a cancellable asyncio.Task and streams its results.
        """
        print(session_id)
        queue = asyncio.Queue()

        async def producer():
            """
            This is the coroutine that will be run as a background task.
            Its job is to consume the async generator and put items in the queue.
            """
            try:
                
                async for item in self._stream_response_sse(user_prompt, model_id, session_id):
                    await queue.put(item)
            except asyncio.CancelledError:
                
                logger.info(f"Task for session {session_id} was cancelled by request.")
                cancelled_payload = {"type": "error", "message": "Task was cancelled by user."}
                cancelled_event = f"data: {json.dumps(cancelled_payload)}\n\n".encode('utf-8')
                await queue.put(cancelled_event)
            except Exception as e:
                
                logger.error(f"Error during SSE generation for session {session_id}: {e}", exc_info=True)
                error_payload = {"type": "error", "message": f"An unexpected error occurred: {e}"}
                error_event = f"data: {json.dumps(error_payload)}\n\n".encode('utf-8')
                await queue.put(error_event)
            finally:
                
                await queue.put(None)

        task = asyncio.create_task(producer())
        RUNNING_ASYNC_TASKS[session_id] = task
        logger.info(f"Task for session {session_id} started and stored.")

        while True:
            item = await queue.get()
            if item is None:
                break
            yield item
            queue.task_done()
        logger.info(
            f"Streaming finished for session {session_id}. Task remains in registry until cancelled or replaced.")

    async def consume_generator(self, generator):
        """Helper to consume an async generator into a list."""
        return [item async for item in generator]

    def stream_response_from_queue(self, queue):
        """
        This is the generator that the StreamingHttpResponse will use.
        It yields items from the queue as they become available.
        """
        while True:
            item = queue.get()
            if item is None:  
                break
            yield item

    async def _handle_request_async(self, request):
        """A helper to handle both GET and POST after validation."""
        serializer = PromptRequestSerializer(data=request.GET if request.method == 'GET' else json.loads(request.body))
        if not serializer.is_valid():
            return JsonResponse(serializer.errors, status=400)

        validated_data = serializer.validated_data
        session_id = validated_data['session_id']

        if session_id in RUNNING_ASYNC_TASKS:
            old_task = RUNNING_ASYNC_TASKS[session_id]
            if not old_task.done():
                logger.warning(
                    f"A task for session {session_id} is already running. Cancelling it before starting a new one.")
                old_task.cancel()

        response = StreamingHttpResponse(
            self.stream_wrapper(request, validated_data['prompt'], validated_data['model_id'], session_id),
            content_type='text/event-stream'
        )
        response['X-Accel-Buffering'] = 'no'
        response['Cache-Control'] = 'no-cache'
        return response

    async def post(self, request, *args, **kwargs):
        return await self._handle_request_async(request)

    async def get(self, request, *args, **kwargs):
        return await self._handle_request_async(request)

class FileSystemView(View):
    def get(self, request, *args, **kwargs):
        """
        Lists all files and directories within the AGENT_OUTPUT_DIR.
        """
        try:
            base_path = AGENT_OUTPUT_DIR
            if not os.path.exists(base_path) or not os.path.isdir(base_path):
                return JsonResponse({"error": "Agent output directory not found."}, status=404)

            file_list = []
            for entry in os.scandir(base_path):
                
                if entry.is_file():
                    file_stat = entry.stat()
                    file_list.append({
                        "name": entry.name,
                        "path": entry.name,  
                        "size_bytes": file_stat.st_size,
                        "modified_at": file_stat.st_mtime,
                    })

            file_list.sort(key=lambda x: x['modified_at'], reverse=True)

            return JsonResponse(file_list, safe=False)

        except Exception as e:
            logger.error(f"Error listing files: {e}")
            return JsonResponse({"error": "An error occurred while listing files."}, status=500)

class FileDownloadView(View):
    def get(self, request, *args, **kwargs):
        """
        Serves a file for download from the AGENT_OUTPUT_DIR.
        Expects a 'path' query parameter.
        """
        relative_path = request.GET.get('path')
        if not relative_path:
            return HttpResponseBadRequest("Missing 'path' query parameter.")

        try:
            
            base_path = os.path.realpath(AGENT_OUTPUT_DIR)
            requested_path = os.path.realpath(os.path.join(base_path, relative_path))

            if not requested_path.startswith(base_path):
                
                logger.warning(f"Directory traversal attempt blocked: {relative_path}")
                return HttpResponseBadRequest("Invalid file path.")

            if os.path.exists(requested_path) and os.path.isfile(requested_path):
                
                response = FileResponse(open(requested_path, 'rb'))
                
                response['Content-Disposition'] = f'attachment; filename="{os.path.basename(requested_path)}"'
                return response
            else:
                return HttpResponseNotFound(f"File not found at path: {relative_path}")

        except Exception as e:
            logger.error(f"Error serving file '{relative_path}': {e}")
            return JsonResponse({"error": "An error occurred while serving the file."}, status=500)

class FileContentView(View):
    def get(self, request):
        relative_path = request.GET.get('path')
        if not relative_path:
            return JsonResponse({'error': 'File path not provided'}, status=400)

        base_dir = os.path.abspath(os.path.join(settings.BASE_DIR, 'agent_outputs'))
        absolute_requested_path = os.path.abspath(os.path.join(base_dir, relative_path))

        if not absolute_requested_path.startswith(base_dir):
            logger.warning(f"Directory traversal attempt blocked for path: {relative_path}")
            return JsonResponse({'error': 'Access denied: Invalid path'}, status=403)

        if not os.path.exists(absolute_requested_path) or not os.path.isfile(absolute_requested_path):
            logger.warning(f"File not found at path: {absolute_requested_path}")
            raise Http404("File does not exist.")

        try:
            
            content_type, _ = mimetypes.guess_type(absolute_requested_path)
            if content_type is None:
                content_type = 'application/octet-stream'  

            with open(absolute_requested_path, 'rb') as f:
                binary_content = f.read()

            is_text_based = content_type.startswith('text/') or content_type in ['application/json', 'application/xml']

            if is_text_based:
                
                try:
                    content = binary_content.decode('utf-8')
                    logger.info(f"Successfully decoded {relative_path} as utf-8.")
                except UnicodeDecodeError:
                    logger.warning(f"Failed to decode {relative_path} as utf-8. Falling back to latin-1.")
                    content = binary_content.decode('latin-1')

                response_content_type = f'{content_type}; charset=utf-8'
                return HttpResponse(content, content_type=response_content_type)
            else:
                
                logger.info(f"Serving binary file {relative_path} with content type {content_type}.")
                return HttpResponse(binary_content, content_type=content_type)

        except IOError as e:
            logger.error(f"IOError reading file {absolute_requested_path}: {e}")
            return JsonResponse({'error': 'Could not read file'}, status=500)
        except Exception as e:
            logger.error(f"An unexpected error occurred while serving file {absolute_requested_path}: {e}")
            return JsonResponse({'error': 'An internal error occurred'}, status=500)

class AvailableModelsView(APIView):
    """
    Provides a list of all models from the static JSON file.
    """
    def get(self, request, *args, **kwargs):
        try:
            
            grouped_models = get_available_models_grouped()
            if not grouped_models:
                return Response({"error": "Model list is empty or not found. Please run the generation script."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            return Response(grouped_models, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error serving available models from file: {e}")
            return Response({"error": "Could not retrieve model list."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)