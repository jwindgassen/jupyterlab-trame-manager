import * as React from 'react';
import { Clipboard } from '@jupyterlab/apputils';
import { copyIcon, folderIcon } from '@jupyterlab/ui-components';
import { CommandRegistry } from '@lumino/commands';

export function Info(props: { label: string; value: React.ReactNode }) {
  return (
    <div className="info-container">
      <span className="info-label">{props.label}:</span>
      {typeof props.value === 'object' ? (
        props.value
      ) : (
        <span className="info-value">{props.value}</span>
      )}
    </div>
  );
}

export const commandRegistryInstance: { instance?: CommandRegistry } = {};

export function Path(props: { path: string }) {
  const handleCopy = () => {
    Clipboard.copyToSystem(props.path);
  };

  const handleOpen = async () => {
    console.log(commandRegistryInstance.instance);
    await commandRegistryInstance.instance?.execute('filebrowser:open-path', {
      path: props.path
    });
  };

  return (
    <div className="path-container">
      <div>{props.path}</div>
      <button className="icon-button" onClick={handleCopy}>
        <copyIcon.react tag="span" width="16px" />
      </button>
      <button className="icon-button" onClick={handleOpen}>
        <folderIcon.react tag="span" width="16px" />
      </button>
    </div>
  );
}
