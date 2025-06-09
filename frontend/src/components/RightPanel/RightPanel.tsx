import React, {useState, useEffect, useRef, useCallback} from 'react';
import './RightPanel.css';
import {
    X as CloseIcon,
    Folder,
    FileText as FileMdIcon,
    File as GenericFileIcon,
    Spinner,
    CaretDown,
    CaretRight,
    Code as JsonIcon,
    Link as LinkIcon,
    FilePdf,
    Globe,
    ImageSquare, ArrowClockwise,
    FilePdf as PdfIcon,
} from "@phosphor-icons/react";
import {Document, Page, pdfjs} from 'react-pdf';
import 'react-pdf/dist/esm/Page/AnnotationLayer.css'; // Recommended for annotations/links
import 'react-pdf/dist/esm/Page/TextLayer.css';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import {PrismAsyncLight as SyntaxHighlighter} from 'react-syntax-highlighter';
import {atomDark} from 'react-syntax-highlighter/dist/esm/styles/prism';
import jsonLang from 'react-syntax-highlighter/dist/esm/languages/prism/json';
import markdownLang from 'react-syntax-highlighter/dist/esm/languages/prism/markdown';

pdfjs.GlobalWorkerOptions.workerSrc = '/pdf.worker.min.js';
SyntaxHighlighter.registerLanguage('json', jsonLang);
SyntaxHighlighter.registerLanguage('markdown', markdownLang);


export interface FileSystemItem {
    name: string;
    type: 'file' | 'directory';
    path: string;
    children?: FileSystemItem[];
    lastModified?: string;
    size?: number;
    _isExpanded?: boolean;
    _depth?: number;
}

export interface SourceLink {
    id: string;
    url: string;
    title: string;
    type: string;
    abstract_or_snippet?: string;
    faviconUrl?: string;
}

interface RightPanelProps {
    onClose: () => void,
    artifacts: any[],
    onResize: (newWidth: number) => void,
    initialWidth: number,
    refreshKey: number,
    fileToAutoOpen?: string | null,
    onAutoOpenDone?: () => void
}

const buildTreeFromFlatList = (flatList: any[]): FileSystemItem[] => {
    const tree: FileSystemItem[] = [];
    const map: { [key: string]: FileSystemItem } = {};
    const filesToIgnore = ['master_plan.json'];

    const filteredList = flatList.filter(item => {
        if (!item.name) return true;
        if (filesToIgnore.includes(item.name)) return false;
        return true;
    });

    const processedList = filteredList.map(item => ({
        ...item,
        type: item.type || (item.name && item.name.includes('.') && !item.name.endsWith('.') ? 'file' : 'directory'),
        path: item.path ? (item.path.startsWith('/') ? item.path.substring(1) : item.path) : item.name,
        name: item.name || 'Unknown',
    }));

    processedList.forEach(item => {
        if (!item.path) {
            console.warn("[buildTreeFromFlatList] Item with no path found, skipping:", item);
            return;
        }
        const parts = item.path.split('/');
        let currentPathSoFar = '';
        let parentNodePath = '';

        parts.forEach((part, index) => {
            const isLastPart = index === parts.length - 1;
            currentPathSoFar = currentPathSoFar ? `${currentPathSoFar}/${part}` : part;
            let node = map[currentPathSoFar];

            if (!node) {
                node = {
                    name: isLastPart ? item.name : part,
                    path: currentPathSoFar,
                    type: isLastPart ? item.type : 'directory',
                    children: isLastPart && item.type === 'file' ? undefined : [],
                    _isExpanded: false,
                    ...(isLastPart && {
                        lastModified: item.lastModified,
                        size: item.size,
                    }),
                };
                map[currentPathSoFar] = node;

                if (parentNodePath === '') {
                    if (!tree.find(rootNode => rootNode.path === node.path)) {
                        tree.push(node);
                    }
                } else {
                    const parentNode = map[parentNodePath];
                    if (parentNode && parentNode.type === 'directory' && parentNode.children) {
                        if (!parentNode.children.find(child => child.path === node.path)) {
                            parentNode.children.push(node);
                        }
                    }
                }
            } else if (isLastPart && item.type === 'file') {
                node.type = 'file';
                node.children = undefined;
                node.lastModified = item.lastModified;
                node.size = item.size;
                node.name = item.name;
            }
            parentNodePath = currentPathSoFar;
        });
    });

    const sortItems = (items: FileSystemItem[]) => {
        if (!items) return;
        items.sort((a, b) => {
            if (a.type === 'directory' && b.type === 'file') return -1;
            if (a.type === 'file' && b.type === 'directory') return 1;
            return a.name.localeCompare(b.name);
        });
        items.forEach(item => {
            if (item.children) sortItems(item.children);
        });
    };
    sortItems(tree);
    return tree;
};


const RightPanel: React.FC<RightPanelProps> = ({
                                                   onClose,
                                                   artifacts,
                                                   onResize,
                                                   initialWidth,
                                                   refreshKey,
                                                   fileToAutoOpen,
                                                   onAutoOpenDone
                                               }) => {
    const [directoryTree, setDirectoryTree] = useState<FileSystemItem[]>([]);
    const resizerRef = useRef<HTMLDivElement>(null);
    const [isLoadingFiles, setIsLoadingFiles] = useState(false);
    const [filesError, setFilesError] = useState<string | null>(null);

    const [selectedFile, setSelectedFile] = useState<FileSystemItem | null>(null);
    const [selectedFileContent, setSelectedFileContent] = useState<string>('');
    const [isLoadingFileContent, setIsLoadingFileContent] = useState(false);
    const [numPdfPages, setNumPdfPages] = useState<number | null>(null);
    const [pdfPageNumber, setPdfPageNumber] = useState<number>(1);
    const [activeTab, setActiveTab] = useState<'files' | 'sources'>('files');
    const [sources, setSources] = useState<SourceLink[]>([]);
    const [isLoadingSources, setIsLoadingSources] = useState(false);
    const [sourcesError, setSourcesError] = useState<string | null>(null);
    const onPdfDocumentLoadSuccess = ({numPages}: { numPages: number }) => {
        setNumPdfPages(numPages);
        setPdfPageNumber(1); // Reset to first page on new PDF load
    };
    const handleMouseDown = useCallback((mouseDownEvent: React.MouseEvent<HTMLDivElement>) => {
        mouseDownEvent.preventDefault();
        const startX = mouseDownEvent.clientX;
        const currentStartWidth = initialWidth;
        const handleMouseMove = (mouseMoveEvent: MouseEvent) => {
            const deltaX = mouseMoveEvent.clientX - startX;
            onResize(currentStartWidth - deltaX);
        };
        const handleMouseUp = () => {
            window.removeEventListener('mousemove', handleMouseMove);
            window.removeEventListener('mouseup', handleMouseUp);
            document.body.style.cursor = '';
            document.body.style.userSelect = '';
        };
        window.addEventListener('mousemove', handleMouseMove);
        window.addEventListener('mouseup', handleMouseUp);
        document.body.style.cursor = 'col-resize';
        document.body.style.userSelect = 'none';
    }, [initialWidth, onResize]);
    console.log("[RightPanel] Rendering. Received fileToAutoOpen:", fileToAutoOpen, "| Received refreshKey:", refreshKey);
    const fetchFiles = useCallback(async () => {
        setIsLoadingFiles(true);
        setFilesError(null);
        try {
            const response = await fetch(`/api/files/list/`);
            if (!response.ok) throw new Error(`Failed to fetch file list: ${response.statusText}`);
            const flatListData: any[] = await response.json();
            const treeData = buildTreeFromFlatList(flatListData);
            setDirectoryTree(treeData);
        } catch (err) {
            setFilesError(err instanceof Error ? err.message : 'An unknown error occurred.');
            console.error("Error fetching file list:", err);
        } finally {
            setIsLoadingFiles(false);
        }
    }, []);
    useEffect(() => {
        console.log("[RightPanel] Auto-open effect is running. Checking conditions...");
        console.log(`   - fileToAutoOpen: ${fileToAutoOpen}`);
        console.log(`   - directoryTree length: ${directoryTree.length}`);

        if (fileToAutoOpen && directoryTree.length > 0) {
            console.log(`[RightPanel] Conditions met. Searching for: '${fileToAutoOpen}'.`);
            const findFileByPath = (path: string, items: FileSystemItem[]): FileSystemItem | null => {
                for (const item of items) {
                    // Use .endsWith() for robustness, in case the path includes a directory
                    if (item.path.endsWith(path)) {
                        return item;
                    }
                    if (item.children) {
                        const found = findFileByPath(path, item.children);
                        if (found) return found;
                    }
                }
                return null;
            };

            const fileItem = findFileByPath(fileToAutoOpen, directoryTree);

            if (fileItem) {
                console.log(`[RightPanel] Found file, simulating click: ${fileItem.path}`);
                handleItemClick(fileItem.path);
                onAutoOpenDone(); // Reset the state in parent
            } else {
                console.warn(`[RightPanel] Did not find '${fileToAutoOpen}' in the current tree.`);
            }
        }
    }, [fileToAutoOpen, directoryTree]);




    const fetchFileContent = useCallback(async (filePath: string) => {
        setIsLoadingFileContent(true);
        setSelectedFileContent('');
        setFilesError(null);
        try {
            const response = await fetch(`/api/files/view/?path=${encodeURIComponent(filePath)}`);
            if (!response.ok) {
                let errorText = `Failed to fetch file content: ${response.status} ${response.statusText} for ${filePath}`;
                try { const errorData = await response.json(); if (errorData?.error) errorText = errorData.error; } catch (e) {}
                throw new Error(errorText);
            }
            const text = await response.text();
            setSelectedFileContent(text);
        } catch (err) {
            const errorMessage = err instanceof Error ? err.message : 'Unknown error';
            console.error("Error fetching file content:", err);
            setSelectedFileContent(`Error loading file: ${errorMessage}`);
        } finally {
            setIsLoadingFileContent(false);
        }
    }, []);

    const handleItemClick = useCallback((itemPath: string) => {
        const toggleOrSelect = (items: FileSystemItem[]): FileSystemItem[] => {
            return items.map(currentItem => {
                if (currentItem.path === itemPath) {
                    if (currentItem.type === 'directory') {
                        return {...currentItem, _isExpanded: !currentItem._isExpanded};
                    } else if (currentItem.type === 'file') {
                        setSelectedFile(currentItem);
                        fetchFileContent(currentItem.path);
                        return currentItem;
                    }
                }
                if (currentItem.children) {
                    return {...currentItem, children: toggleOrSelect(currentItem.children)};
                }
                return currentItem;
            });
        };
        setDirectoryTree(prevTree => toggleOrSelect(prevTree));
    }, [fetchFileContent]);

    const fetchRawSources = useCallback(async () => {
        const rawSourcesPath = "raw_sources.json";
            setIsLoadingSources(true);
            setSourcesError(null);
            setSources([]);
            try {
                const response = await fetch(`/api/files/view/?path=${encodeURIComponent(rawSourcesPath)}`);
                if (!response.ok) throw new Error(`Failed to fetch raw_sources.json: ${response.statusText}`);
                const rawJsonString = await response.text();
                const parsedJsonData: Array<{
                    type: string;
                    title: string;
                    URL: string;
                    abstract_or_snippet?: string
                }> = JSON.parse(rawJsonString);

                const extractedLinks: SourceLink[] = parsedJsonData.map((src) => {
                    let faviconUrl = '';
                    if (src.type?.toLowerCase() === 'web' && src.URL) {
                        try {
                            const domain = new URL(src.URL).hostname;
                            faviconUrl = `https://www.google.com/s2/favicons?domain=${domain}&sz=32`;
                        } catch (e) {
                            console.warn(`Could not parse URL to get domain for favicon: ${src.URL}`, e);
                        }
                    }
                    return {
                        id: src.URL,
                        url: src.URL,
                        title: src.title || src.URL,
                        type: src.type || 'unknown',
                        abstract_or_snippet: src.abstract_or_snippet,
                        faviconUrl: faviconUrl,
                    };
                });
                setSources(extractedLinks);
            } catch (err) {
                setSourcesError(err instanceof Error ? err.message : 'Failed to load or parse sources.');
                console.error("Error fetching/parsing raw_sources.json:", err);
            } finally {
                setIsLoadingSources(false);
            }
        }, []);


    useEffect(() => {
        fetchFiles();
    }, [fetchFiles]);

        useEffect(() => {
            if (refreshKey === 0) return;

            console.log("[RightPanel] Refresh key changed, re-fetching file list.");
            fetchFiles();

            if (selectedFile && selectedFile.name === 'master_plan.md') {
                console.log("[RightPanel] master_plan.md is open, refreshing its content.");
                fetchFileContent(selectedFile.path);
            }
        }, [refreshKey, fetchFiles, selectedFile, fetchFileContent]);

        useEffect(() => {
            if (activeTab === 'sources') {
                fetchRawSources();
            }
        }, [activeTab, fetchRawSources, refreshKey]);

        // --- FIX: This effect is now stable and will work correctly ---
        useEffect(() => {
            if (fileToAutoOpen && directoryTree.length > 0 && onAutoOpenDone) {
                const findAndOpenFile = (path: string, items: FileSystemItem[]): boolean => {
                    for (const item of items) {
                        if (item.path === path) {
                            handleItemClick(item.path);
                            onAutoOpenDone();
                            return true;
                        }
                        if (item.children) {
                            if (findAndOpenFile(path, item.children)) return true;
                        }
                    }
                    return false;
                };
                findAndOpenFile(fileToAutoOpen, directoryTree);
            }
        }, [directoryTree, fileToAutoOpen, onAutoOpenDone, handleItemClick]);
    const renderItemsRecursive = (items: FileSystemItem[], depth = 0): JSX.Element[] => {
            if (!items || items.length === 0) return [];
            return items.map((item) => {
                const isSelected = selectedFile?.path === item.path;
                const isMarkdown = item.name.endsWith('.md') || item.name.endsWith('.markdown');
                const isJson = item.name.endsWith('.json');
                const isPdf = item.name.toLowerCase().endsWith('.pdf'); // Check for PDF

                let icon;
                if (item.type === 'directory') {
                    icon = <Folder size={18} weight={item._isExpanded ? "fill" : "regular"} className="icon-directory"/>;
                } else if (isPdf) { // Add case for PDF icon
                    icon = <PdfIcon size={18} className="icon-pdf"/>;
                } else if (isMarkdown) {
                    icon = <FileMdIcon size={18} className="icon-markdown"/>;
                } else if (isJson) {
                    icon = <JsonIcon size={18} weight="bold" className="icon-json"/>;
                } else {
                    icon = <GenericFileIcon size={18} className="icon-file-generic"/>;
                }
                return (
                    <React.Fragment key={item.path}>
                        <li
                            className={`file-item type-${item.type} ${isSelected ? 'selected' : ''}`}
                            style={{paddingLeft: `${depth * 18 + 8}px`}}
                            onClick={() => handleItemClick(item.path)}
                            title={item.path}
                        >
                            <span className="item-icon-wrapper">{icon}</span>
                            <span className="item-name">{item.name}</span>
                            {item.type === 'directory' && item.children && item.children.length > 0 && (
                                <span className={`caret ${item._isExpanded ? 'expanded' : ''}`}>
                                {item._isExpanded ? <CaretDown size={14} weight="bold"/> :
                                    <CaretRight size={14} weight="bold"/>}
                            </span>
                            )}
                        </li>
                        {item.type === 'directory' && item._isExpanded && item.children && item.children.length > 0 && (
                            renderItemsRecursive(item.children, depth + 1)
                        )}
                    </React.Fragment>
                );
            });
        };
        const getSourceIcon = (source: SourceLink) => {
            if (source.faviconUrl) {
                return (
                    <img
                        src={source.faviconUrl}
                        alt=""
                        className="source-favicon"
                        onError={(e) => {
                            (e.target as HTMLImageElement).style.display = 'none';
                        }}
                    />
                );
            }
            const type = source.type?.toLowerCase() || '';
            if (type.includes('pdf')) return <FilePdf size={18} className="icon-source-pdf"/>;
            if (type.includes('web') || type.includes('html') || type.includes('link')) return <Globe size={18}
                                                                                                      className="icon-source-web"/>;
            return <LinkIcon size={18} className="icon-source-generic"/>;
        };

    return (
        <aside className="right-panel">
            <div ref={resizerRef} className="resizer-handle" onMouseDown={handleMouseDown} title="Resize panel"/>
            <div className="right-panel-header">
                <h3>{activeTab === 'files' ? 'File Workspace' : 'Referenced Sources'}</h3>
                <div className="panel-header-actions">
                    {activeTab === 'files' && (
                        <button
                            onClick={fetchFiles}
                            className="panel-action-button refresh-button"
                            title="Refresh file list"
                            disabled={isLoadingFiles}
                        >
                            <ArrowClockwise
                                size={18}
                                weight={isLoadingFiles ? "bold" : "regular"}
                                className={isLoadingFiles ? "spinning" : ""}
                            />
                        </button>
                    )}
                    <button onClick={onClose} title="Close Panel" className="panel-action-button close-panel-button">
                        <CloseIcon size={20}/>
                    </button>
                </div>
            </div>

            <div className="right-panel-tabs">
                <button className={`tab-button ${activeTab === 'files' ? 'active' : ''}`}
                        onClick={() => setActiveTab('files')}>Files
                </button>
                <button className={`tab-button ${activeTab === 'sources' ? 'active' : ''}`}
                        onClick={() => setActiveTab('sources')}>Sources
                </button>
            </div>

            <div className="right-panel-content">
                {activeTab === 'files' && (
                    <>
                        <div className="file-browser-section">
                            <h4>agent_outputs</h4>
                            {isLoadingFiles &&
                                <div className="loading-spinner"><Spinner size={24}/> Loading files...</div>}
                            {filesError && <div className="error-message">Error: {filesError}</div>}
                            {!isLoadingFiles && !filesError && directoryTree.length === 0 &&
                                <p>No files or folders found.</p>}
                            {!isLoadingFiles && !filesError && directoryTree.length > 0 && (
                                <ul className="file-list">{renderItemsRecursive(directoryTree)}</ul>
                            )}
                        </div>
                        <div className="file-preview-section">
                            <h4>Preview</h4>
                            {selectedFile ? (
                                <>
                                    <div className="file-info"><strong>{selectedFile.name}</strong></div>
                                    {isLoadingFileContent &&
                                        <div className="loading-spinner"><Spinner size={24}/> Loading content...</div>}
                                    {!isLoadingFileContent && selectedFileContent && (
                                        <>
                                            {selectedFile.name.toLowerCase().endsWith('.pdf') ? (
                                                <div className="pdf-content-preview">
                                                    <Document
                                                        file={`/api/files/view/?path=${encodeURIComponent(selectedFile.path)}`}
                                                        onLoadSuccess={onPdfDocumentLoadSuccess}
                                                        onLoadError={console.error}
                                                        loading={<div className="loading-spinner"><Spinner
                                                            size={24}/> Loading PDF...</div>}
                                                        className="pdf-document-container"
                                                    >
                                                        <Page pageNumber={pdfPageNumber} className="pdf-page"/>
                                                    </Document>
                                                    {numPdfPages && (
                                                        <div className="pdf-pagination">
                                                            <button disabled={pdfPageNumber <= 1}
                                                                    onClick={() => setPdfPageNumber(pdfPageNumber - 1)}>
                                                                Previous
                                                            </button>
                                                            <span>
                                                                Page {pdfPageNumber} of {numPdfPages}
                                                            </span>
                                                            <button disabled={pdfPageNumber >= numPdfPages}
                                                                    onClick={() => setPdfPageNumber(pdfPageNumber + 1)}>
                                                                Next
                                                            </button>
                                                        </div>
                                                    )}
                                                </div>
                                            ) : (selectedFile.name.endsWith('.md') || selectedFile.name.endsWith('.markdown')) ? (
                                                <div className="markdown-content-preview">
                                                    <ReactMarkdown
                                                        children={selectedFileContent}
                                                        remarkPlugins={[remarkGfm]}
                                                        components={{
                                                            code({node, inline, className, children, ...props}) {
                                                                const match = /language-(\w+)/.exec(className || '');
                                                                return !inline && match ? (
                                                                    <SyntaxHighlighter style={atomDark}
                                                                                       language={match[1]}
                                                                                       PreTag="div" {...props}>{String(children).replace(/\n$/, '')}</SyntaxHighlighter>
                                                                ) : (<code
                                                                    className={className} {...props}>{children}</code>);
                                                            }
                                                        }}
                                                    />
                                                </div>
                                            ) : selectedFile.name.endsWith('.json') ? (
                                                <div className="json-content-preview">
                                                    <SyntaxHighlighter language="json" style={atomDark} wrapLines={true}
                                                                       showLineNumbers={false}
                                                                       PreTag="div">{selectedFileContent}</SyntaxHighlighter>
                                                </div>
                                            ) : (
                                                <pre className="file-content-preview">{selectedFileContent}</pre>
                                            )}
                                        </>
                                    )}
                                    {!isLoadingFileContent && !selectedFileContent && !filesError && ( // Use filesError here
                                        <div className="preview-message-placeholder">
                                            <p>File is empty or content could not be displayed.</p>
                                        </div>
                                    )}
                                </>
                            ) : (
                                <div className="preview-message-placeholder">
                                    <p className="no-file-selected">Select a file to preview its content.</p>
                                </div>
                            )}
                        </div>
                    </>
                )}

                {activeTab === 'sources' && (
                    <div className="sources-section">
                        <h4>Referenced Sources</h4>
                        {isLoadingSources &&
                            <div className="loading-spinner"><Spinner size={24}/> Loading sources...</div>}
                        {sourcesError && <div className="error-message">Error: {sourcesError}</div>}
                        {!isLoadingSources && !sourcesError && sources.length === 0 && <p>No sources found.</p>}
                        {!isLoadingSources && !sourcesError && sources.length > 0 && (
                            <ul className="sources-list">
                                {sources.map(source => (
                                    <li key={source.id} className="source-item"
                                        title={source.abstract_or_snippet || source.url}>
                                        <a href={source.url} target="_blank" rel="noopener noreferrer">
                                            <span className="item-icon-wrapper source-icon-wrapper">
                                                {getSourceIcon(source)}
                                                <ImageSquare size={16} className="source-favicon-placeholder-fallback"/>
                                            </span>
                                            <span className="item-name source-title">{source.title}</span>
                                        </a>
                                        {source.abstract_or_snippet && (
                                            <p className="source-snippet">{source.abstract_or_snippet}</p>
                                        )}
                                    </li>
                                ))}
                            </ul>
                        )}
                    </div>
                )}
            </div>
        </aside>
    );
};

export default RightPanel;