import React from 'react';
import './ModelSelector.css';
import { Cube } from "@phosphor-icons/react";

// Define the shape of your model data
export interface Model {
    provider: string;
    id: string;
    name: string;
}

export interface GroupedModels {
    [provider: string]: Model[];
}

// Define the props the component will accept
interface ModelSelectorProps {
    models: GroupedModels;
    selectedModelId: string;
    onModelChange: (modelId: string) => void;
    isLoading: boolean;
}

const ModelSelector: React.FC<ModelSelectorProps> = ({ models, selectedModelId, onModelChange, isLoading }) => {
    return (
        <div className="model-selector-container">
            <Cube size={18} className="model-selector-icon" />
            <select
                className="model-selector-dropdown custom-scrollbar"
                value={selectedModelId}
                onChange={(e) => onModelChange(e.target.value)}
                disabled={isLoading || Object.keys(models).length === 0}
            >
                {isLoading ? (
                    <option>Loading models...</option>
                ) : (
                    Object.entries(models).map(([provider, modelList]) => (
                        <optgroup key={provider} label={provider}>
                            {modelList.map((model) => (
                                <option key={model.id} value={model.id}>
                                    {model.name}
                                </option>
                            ))}
                        </optgroup>
                    ))
                )}
                {!isLoading && Object.keys(models).length === 0 && (
                    <option>No models available</option>
                )}
            </select>
        </div>
    );
};

export default ModelSelector;