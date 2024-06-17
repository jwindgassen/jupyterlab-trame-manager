import * as React from 'react';
import { Clipboard } from '@jupyterlab/apputils';
import { copyIcon, folderIcon } from '@jupyterlab/ui-components';
import { CommandRegistry } from '@lumino/commands';

export function Info(props: { label: string; value: React.ReactNode }) {
  return (
    <div>
      <span className="info-label">{props.label}:</span>
      &nbsp;
      {props.value}
    </div>
  );
}

export const commandRegistryInstance: { instance?: CommandRegistry } = {};

export function Path(props: { path: string }) {
  const handleCopy = () => {
    Clipboard.copyToSystem(props.path);
  };

  const handleOpen = async () => {
    await commandRegistryInstance.instance?.execute('filebrowser:open', {
      path: props.path
    });
  };

  return (
    <div className="path-container">
      <div>{props.path}</div>
      <button className="iconButton" onClick={handleCopy}>
        <copyIcon.react tag="span" width="16px" />
      </button>
      <button className="iconButton" onClick={handleOpen}>
        <folderIcon.react tag="span" width="16px" />
      </button>
    </div>
  );
}
