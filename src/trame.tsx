import { URLExt } from '@jupyterlab/coreutils';
import { showDialog, showErrorMessage } from '@jupyterlab/apputils';
import * as React from 'react';
import Collapsible from 'react-collapsible';

import { Info, Empty, InstanceList } from './components';
import { requestAPI } from './handler';
import { TrameLauncherDialog } from './dialogs';


type TrameAppOptions = {
  name: string;
  displayName: string;
  path: string;
  instances: TrameInstanceOptions[];
};

export type TrameLaunchOptions = {
  name: string;
  dataDirectory: string;
}

type TrameInstanceOptions = TrameLaunchOptions & {
  port: number;
  base_url: string;
  log: string;
};


class TrameAppInstance extends React.Component<TrameInstanceOptions> {
  constructor(props: TrameInstanceOptions) {
    super(props);
  }

  openInstance = () => {
    const url = URLExt.join(this.props.base_url, 'index.html');
    window.open(url, '_blank', 'noreferrer');
  };

  render() {
    const title = <>
      <b>{this.props.name}</b>
    </>

    return (
      <li>
        <div style={{ flexGrow: 1 }}>
          <Collapsible trigger={title} >
            <Info label='Data Directory' value={`${this.props.dataDirectory}`} />
            <Info label='Port' value={`${this.props.port}`} />
            <Info label='Base URL' value={`${this.props.base_url}`} />
            <Info label='Log File' value={this.props.log} />
          </Collapsible>
        </div>

        <button className='open-button' onClick={this.openInstance}>Open</button>
      </li>
    );
  }
}


class TrameApp extends React.Component<TrameAppOptions, InstanceList<TrameInstanceOptions>> {
  constructor(props: TrameAppOptions) {
    super(props);
    this.state = {
      instances: this.props.instances  // Initialize with existing instances. ToDo: Improve?
    };
  }

  launchInstance = async () => {
    const options = await showDialog({
      title: 'Launch a new ParaView instance',
      body: new TrameLauncherDialog(this.props.displayName, this.state.instances.length)
    });
    console.log('Launching trame app:', options.value);

    const instance = await requestAPI<TrameInstanceOptions>('trame', {
      method: 'POST',
      body: JSON.stringify({
        appName: this.props.name,
        ...options.value
      })
    });

    this.setState({
      instances: [...this.state.instances, instance]
    });
    await showErrorMessage('Success', `Launched new trame instance on port ${instance.port}`);
  };

  render() {
    const title = (
      <div>
        <b> {this.props.displayName} </b><br />
        Running Instances: {this.state.instances.length}
      </div>
    );

    return (
      <>
        <Collapsible trigger={title}>
          <Info label='Path' value={this.props.path} />

          <div style={{ height: '40px', margin: '10px 0 0 0' }}>
            <button className='launch-button' onClick={this.launchInstance}>Launch</button>
          </div>

          <div className='instance-list'>
            {this.state.instances.map(instance => (
              <TrameAppInstance {...instance} />
            ))}
          </div>
        </Collapsible>
      </>
    );
  }
}


export class TrameSidepanelSegment extends React.Component<Empty, InstanceList<TrameAppOptions>> {
  constructor() {
    super({});
    this.state = { instances: [] };
  }

  async componentDidMount() {
    await this.fetchData();
  }

  fetchData = async () => {
    this.setState({
      instances: await requestAPI<TrameAppOptions[]>('trame')
    });
  };

  render() {
    return (
      <>
        <h3>trame Apps:</h3>
        <div id='trame-instances' className='instance-list'>
          {this.state.instances.map((app) => (
            <TrameApp {...app} />
          ))}
        </div>
      </>
    );
  }
}
