
import React from 'react';
import { Folder, FileText as FileMdIcon, File as GenericFileIcon, CaretDown, CaretRight } from "@phosphor-icons/react";
import type { FileSystemItem as FSType } from './RightPanel'; 

interface FileBrowserItemProps {
    item: FSType;
    depth: number;
    isSelected: boolean;
    onItemClick: (path: string) => void;
    renderRecursive: (items: FSType[], depth: number) => JSX.Element[]; 
}

const FileBrowserItem: React.FC<FileBrowserItemProps> = React.memo(({
                                                                        item,
                                                                        depth,
                                                                        isSelected,
                                                                        onItemClick,
                                                                        renderRecursive
                                                                    }) => {
    
    const isMarkdown = item.name.endsWith('.md') || item.name.endsWith('.markdown');
    let icon;

    if (item.type === 'directory') {
        icon = <Folder size={18} weight={item._isExpanded ? "fill" : "regular"} className="icon-directory" />;
    } else if (isMarkdown) {
        icon = <FileMdIcon size={18} className="icon-markdown" />;
    } else {
        icon = <GenericFileIcon size={18} className="icon-file-generic" />;
    }

    return (
        <React.Fragment>
            <li
                className={`file-item type-${item.type} ${isSelected ? 'selected' : ''}`}
                style={{ paddingLeft: `${depth * 18 + 8}px` }}
                onClick={() => onItemClick(item.path)}
                title={item.path}
            >
                <span className="item-icon-wrapper">{icon}</span>
                <span className="item-name">{item.name}</span>
                {item.type === 'directory' && item.children && item.children.length > 0 && (
                    <span className={`caret ${item._isExpanded ? 'expanded' : ''}`}>
            {item._isExpanded ?
                <CaretDown size={14} weight="bold" /> :
                <CaretRight size={14} weight="bold" />
            }
          </span>
                )}
            </li>
            {item.type === 'directory' && item._isExpanded && item.children && item.children.length > 0 && (
                renderRecursive(item.children, depth + 1)
            )}
        </React.Fragment>
    );
});

export default FileBrowserItem;