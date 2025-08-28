'use client';

import React from 'react';
import CodeMirror from '@uiw/react-codemirror';
import { yaml } from '@codemirror/lang-yaml';
import { EditorView } from '@codemirror/view';

interface YamlEditorProps {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  readOnly?: boolean;
  height?: string;
  className?: string;
}

const YamlEditor: React.FC<YamlEditorProps> = ({
  value,
  onChange,
  placeholder = 'Enter YAML configuration...',
  readOnly = false,
  height = '300px',
  className = ''
}) => {
  const extensions = [
    yaml(),
    EditorView.theme({
      '&': {
        fontSize: '14px',
      },
      '.cm-content': {
        padding: '16px',
      },
      '.cm-focused': {
        outline: 'none',
      },
      '.cm-editor': {
        borderRadius: '6px',
        backgroundColor: '#ffffff',
      },
      '.cm-scroller': {
        fontFamily: 'ui-monospace, SFMono-Regular, "SF Mono", Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace',
      },
    }),
  ];

  return (
    <div className={`border border-gray-300 rounded-md overflow-hidden ${className}`}>
      <CodeMirror
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        readOnly={readOnly}
        height={height}
        extensions={extensions}
        basicSetup={{
          lineNumbers: true,
          foldGutter: true,
          dropCursor: false,
          allowMultipleSelections: false,
          indentOnInput: true,
          bracketMatching: true,
          closeBrackets: true,
          autocompletion: true,
          highlightSelectionMatches: false,
        }}
      />
    </div>
  );
};

export default YamlEditor;