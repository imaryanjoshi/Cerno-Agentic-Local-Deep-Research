// src/data/homePageFeatures.ts
// src/data/homePageFeatures.ts
import type {Icon} from '@phosphor-icons/react'; // Import base type if needed for icon prop
// Import base type if needed for icon prop
import { Brain, ShootingStar, TerminalWindow, ChartLineUp, Lightning } from "@phosphor-icons/react";
import React from "react"; // Import specific icons

export interface FeatureItemData {
    id: string;
    initialIcon: Icon; // Phosphor icon component
    initialTitle: string;
    // Initial grid position (conceptual, for your reference, not directly used in simple rendering yet)
    // gridRowStart?: number;
    // gridColStart?: number;

    bentoHeadline: string;
    bentoVisual?: React.FC; // Component for the visual in the bento cell
    bentoText: string;
    bentoKeywords?: string[];
    bentoCellClass?: string; // For specific bento grid cell sizing/styling
}

// Placeholder for bento visuals - create simple ones for now
const SmartContextVisual = () => <div className="bento-visual-placeholder">Smart Context Demo</div>;
const CreativeAIVisual = () => <div className="bento-visual-placeholder">Creative AI Output</div>;
const DevToolsVisual = () => <div className="bento-visual-placeholder">Dev Tools Integration</div>;
const DataInsightsVisual = () => <div className="bento-visual-placeholder">Data Insights Graph</div>;
const TaskAutomationVisual = () => <div className="bento-visual-placeholder">Task Automation Flow</div>;


export const featuresData: FeatureItemData[] = [
    {
        id: 'smart-context',
        initialIcon: Brain,
        initialTitle: 'Smart Context',
        // gridRowStart: 1, gridColStart: 1,
        bentoHeadline: "Understands You, Remembers Everything.",
        bentoVisual: SmartContextVisual,
        bentoText: "Our AI builds deep understanding of your work, preferences, and history for truly contextual assistance.",
        bentoKeywords: ['Contextual Memory', 'Personalized AI'],
        bentoCellClass: 'bento-cell-large', // Example class for the large cell
    },
    {
        id: 'creative-ai',
        initialIcon: ShootingStar,
        initialTitle: 'Creative AI',
        // gridRowStart: 1, gridColStart: 4,
        bentoHeadline: "Your Creative Co-Pilot.",
        bentoVisual: CreativeAIVisual,
        bentoText: "Draft compelling copy, generate code, or brainstorm innovative ideas effortlessly.",
        bentoCellClass: 'bento-cell-medium',
    },
    {
        id: 'dev-tools',
        initialIcon: TerminalWindow,
        initialTitle: 'Dev Tools',
        // gridRowStart: 2, gridColStart: 1,
        bentoHeadline: "Supercharge Your Development.",
        bentoVisual: DevToolsVisual,
        bentoText: "Integrated tools: code generation, debugging, documentation, and direct shell access.",
        bentoCellClass: 'bento-cell-medium',
    },
    {
        id: 'data-insights',
        initialIcon: ChartLineUp,
        initialTitle: 'Data Insights',
        // gridRowStart: 2, gridColStart: 4,
        bentoHeadline: "Uncover Actionable Intelligence.",
        bentoVisual: DataInsightsVisual,
        bentoText: "Connect data sources, let our AI analyze trends, and get smarter decision-making insights.",
        bentoCellClass: 'bento-cell-medium',
    },
    {
        id: 'task-automation',
        initialIcon: Lightning,
        initialTitle: 'Task Automation',
        // gridRowStart: 4, gridColStart: 2, // Example conceptual position
        bentoHeadline: "Automate the Mundane, Focus on Impact.",
        bentoVisual: TaskAutomationVisual,
        bentoText: "Delegate repetitive tasks and complex workflows, freeing you for strategic work.",
        bentoCellClass: 'bento-cell-medium',
    }
];