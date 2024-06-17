import React, { createContext, useContext, useEffect } from 'react';
import Collapsible from 'react-collapsible';
import { showDialog, showErrorMessage } from '@jupyterlab/apputils';
import { refreshIcon } from '@jupyterlab/ui-components';

import { requestAPI, useAPI } from './handler';
import { ParaViewLauncherDialog } from './dialogs';
import { Info } from './components';

export type ParaViewLaunchOptions = {
  name: string;
  account: string;
  partition: string;
  nodes: number;
  timeLimit: string;
};

export type ParaViewInstanceOptions = ParaViewLaunchOptions & {
  state: string;
  timeUsed: string;
};

type ParaViewReturnStatus = {
  returnCode: number;
  message: string;
};

const RefreshTimeout = 30 * 1000; // 30 Seconds
const ParaViewContext = createContext<ParaViewInstanceOptions[]>([]);

function ParaViewInstance({ index }: { index: number }) {
  const { name, account, nodes, partition, state, timeLimit, timeUsed } =
    useContext(ParaViewContext)[index];

  const label = (
    <>
      <b>{name}</b>
      <Info label="Nodes" value={nodes.toString()} />
      <Info label="Status" value={state} />
      <Info label="Time" value={`${timeUsed} / ${timeLimit}`} />
    </>
  );

  return (
    <>
      <Collapsible trigger={label}>
        <Info label="Project" value={account} />
        <Info label="Partition" value={partition} />
        <Info label="Nodes" value={nodes.toString()} />
      </Collapsible>
    </>
  );
}

export default function ParaViewSidepanelSegment() {
  const [instances, refresh] = useAPI<ParaViewInstanceOptions[]>('paraview');

  useEffect(() => {
    const handle = setInterval(refresh, RefreshTimeout);
    return () => clearInterval(handle);
  }, []);

  async function newInstance() {
    const options = await showDialog({
      title: 'Launch a new ParaView instance',
      body: new ParaViewLauncherDialog()
    });
    console.log(options.value);

    const status = await requestAPI<ParaViewReturnStatus>('paraview', {
      method: 'POST',
      body: JSON.stringify(options.value)
    });

    await showErrorMessage(
      status.returnCode === 0 ? 'Success' : 'Error',
      status.message
    );
  }

  return (
    <>
      <h3>Running ParaView backends:</h3>
      <span className="toolbar">
        <button className="icon-button" onClick={refresh}>
          <refreshIcon.react tag="div" width="20px" />
        </button>
        <button className="launch-button" onClick={newInstance}>
          Launch
        </button>
      </span>
      <div id="paraview-instances" className="instance-list">
        <ParaViewContext.Provider value={instances ?? []}>
          {instances?.map((_, idx) => <ParaViewInstance index={idx} />)}
        </ParaViewContext.Provider>
      </div>
    </>
  );
}
