import { URLExt } from '@jupyterlab/coreutils';
import {
  showDialog,
  showErrorMessage,
  InputDialog
} from '@jupyterlab/apputils';
import React, { useState, createContext, useContext, useEffect } from 'react';
import Collapsible from 'react-collapsible';

import { Info, Path } from './components';
import { requestAPI, useAPI } from './handler';
import { TrameLauncherDialog } from './dialogs';
import { ParaViewInstanceOptions } from './paraview';

type TrameAppOptions = {
  name: string;
  displayName: string;
  path: string;
  instances: TrameInstanceOptions[];
};

type TrameInstanceOptions = {
  name: string;
  dataDirectory: string;
  port: number;
  base_url: string;
  log: string;
};

export type TrameLaunchOptions = Pick<
  TrameInstanceOptions,
  'name' | 'dataDirectory'
>;

type TrameInstanceProps = {
  appName: string;
  appIndex: number;
  instanceIndex: number;
};

const RefreshTimeout = 30 * 1000; // 30 Seconds
const TrameContext = createContext<TrameAppOptions[]>([]);

function TrameAppInstance({
  appName,
  appIndex,
  instanceIndex
}: TrameInstanceProps) {
  const { base_url, dataDirectory, log, name, port } =
    useContext(TrameContext)[appIndex].instances[instanceIndex];
  const [connection, setConnection] = useState<[string, string] | null>(null);

  function openInstance() {
    window.open(base_url, '_blank', 'noreferrer');
  }

  async function connect() {
    const servers = await requestAPI<ParaViewInstanceOptions[]>('paraview');

    const serverName = await InputDialog.getItem({
      title: 'Select ParaView Server to connect to',
      items: servers.map(s => s.name),
      current: 0,
      editable: false
    });

    if (!serverName.value || serverName.value.length === 0) {
      return;
    }
    console.log(
      `Connecting instance '${name}' to Server '${serverName.value}'`
    );

    const response = await requestAPI<{ url: string }>(
      URLExt.join('trame', 'connect'),
      {
        method: 'POST',
        body: JSON.stringify({
          appName: appName,
          instanceName: name,
          serverName: serverName.value
        })
      }
    );

    setConnection([serverName.value, response.url]);
  }

  async function disconnect() {
    await requestAPI(URLExt.join('trame', 'disconnect'), {
      method: 'POST',
      body: JSON.stringify({
        appName: appName,
        instanceName: name
      })
    });

    setConnection(null);
  }

  const title = (
    <>
      <b>{name}</b>
    </>
  );

  const connectButton = connection ? (
    <div style={{ marginTop: '10px' }}>
      Connected to ParaView Server&nbsp;
      <span style={{ fontWeight: 'bold' }}>{connection[0]}</span>
      &nbsp;on&nbsp;
      <span style={{ fontWeight: 'bold' }}>{connection[1]}:11111</span>
      <button className="disconnect-button" onClick={disconnect}>
        Disconnect
      </button>
    </div>
  ) : (
    <button className="connect-button" onClick={connect}>
      Connect
    </button>
  );

  return (
    <li>
      <div style={{ flexGrow: 1 }}>
        <Collapsible trigger={title}>
          <Info label="Data Directory" value={<Path path={dataDirectory} />} />
          <Info label="Port" value={`${port}`} />
          <Info label="Base URL" value={`${base_url}`} />
          <Info label="Log File" value={<Path path={log} />} />
          {connectButton}
        </Collapsible>
      </div>

      <button className="open-button" onClick={openInstance}>
        Open
      </button>
    </li>
  );
}

function TrameApp({ index }: { index: number }) {
  const { displayName, name, path, instances } =
    useContext(TrameContext)[index];

  async function launchInstance() {
    const options = await showDialog({
      title: 'Launch a new ParaView instance',
      body: new TrameLauncherDialog(displayName, instances.length)
    });
    console.log('Launching trame app:', options.value);

    const instance = await requestAPI<TrameInstanceOptions>('trame', {
      method: 'POST',
      body: JSON.stringify({
        appName: name,
        ...options.value
      })
    });

    await showErrorMessage(
      'Success',
      `Launched new trame instance on port ${instance.port}`
    );
  }

  const title = (
    <div>
      <b> {displayName} </b>
      <br />
      Running Instances: {instances.length}
    </div>
  );

  return (
    <>
      <Collapsible trigger={title}>
        <Info label="Path" value={<Path path={path} />} />

        <div style={{ height: '40px', margin: '10px 0 0 0' }}>
          <button className="launch-button" onClick={launchInstance}>
            Launch
          </button>
        </div>

        <div className="instance-list">
          {instances.map((_, idx) => (
            <TrameAppInstance
              appName={name}
              appIndex={index}
              instanceIndex={idx}
            />
          ))}
        </div>
      </Collapsible>
    </>
  );
}

export default function TrameSidepanelSegment() {
  const [instances, refresh] = useAPI<TrameAppOptions[]>('trame');

  useEffect(() => {
    const handle = setInterval(refresh, RefreshTimeout);
    return () => clearInterval(handle);
  }, []);

  return (
    <>
      <h3>trame Apps:</h3>
      <div id="trame-instances" className="instance-list">
        <TrameContext.Provider value={instances ?? []}>
          {instances?.map((_, idx) => <TrameApp index={idx} />)}
        </TrameContext.Provider>
      </div>
    </>
  );
}
