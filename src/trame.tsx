import { URLExt } from '@jupyterlab/coreutils';
import { ServerConnection } from '@jupyterlab/services';
import { showErrorMessage } from '@jupyterlab/apputils';
import * as React from 'react';
import Collapsible from 'react-collapsible';

import { Info, Empty, InstanceList } from './components';
import { requestAPI } from './handler';


type TrameAppOptions = {
  name: string;
  displayName: string;
  path: string;
  instances: TrameInstanceOptions[];
};

type TrameInstanceOptions = {
  port: number;
  log: string;
};


class TrameAppInstance extends React.Component<TrameInstanceOptions> {
  constructor(props: TrameInstanceOptions) {
    super(props);
  }

  openInstance = () => {
    const settings = ServerConnection.makeSettings();
    const url = URLExt.join(settings.baseUrl, 'proxy', String(this.props.port), 'index.html');
    window.open(url, '_blank', 'noreferrer');
  };

  render() {
    return (
      <li>
        <div style={{ flexGrow: 1 }}>
          <Info label='Port' value={`${this.props.port}`} />
          <Info label='Log File' value={this.props.log} />
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
    console.log('Launching trame app ' + this.props.name);

    const instance = await requestAPI<TrameInstanceOptions>('trame', {
      method: 'POST',
      body: JSON.stringify({
        app_name: this.props.name
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
        <b> {this.props.name} </b><br />
        Running Instances: {this.state.instances.length}
      </div>
    );

    return (
      <>
        <Collapsible trigger={title}>
          <Info label='Path' value={this.props.path} />

          <h4>
            Instances:
            <button className='launch-button' onClick={this.launchInstance}>Launch</button>
          </h4>
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
