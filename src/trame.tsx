import { URLExt } from '@jupyterlab/coreutils';
import { ServerConnection } from '@jupyterlab/services';
import { showErrorMessage } from '@jupyterlab/apputils'
import * as React from 'react';
import Collapsible from 'react-collapsible';
import { Info } from './components';
import { requestAPI } from './handler';


type TrameAppOptions = {
  name: string;
  displayName: string;
  path: string;
  instances: string[];
};

type TrameInstanceOptions = {
  name: string;
  path: string;
  url: string;
};


class TrameAppInstance extends React.Component<TrameInstanceOptions> {
  constructor(props: TrameInstanceOptions) {
    super(props);
  }

  openInstance = () => {
    window.open(this.props.url, '_blank', 'noreferrer');
  };

  render() {
    return (
      <div>
        <Collapsible trigger="State: Running">
          <Info label="Connected To Backend" value={this.props.url} />
          <Info label="Root Directory" value={this.props.path} />
        </Collapsible>
        <button onClick={this.openInstance}>Open</button>
      </div>
    );
  }
}


class TrameApp extends React.Component<{name: string, path: string}, {instances: string[]}> {
  constructor(props: {name: string, path: string}) {
    super(props);
    this.state = {
      instances: []
    }
  }
    
  launchInstance = async () => {
    console.log('Launching trame app ' + this.props.name)

    const response = await requestAPI<{port: number}>('trame', {
      method: 'POST',
      body: JSON.stringify({
        app_name: this.props.name
      })
    });
    
    const settings = ServerConnection.makeSettings();
    // Use JupyterServerproxy for now
    const url = URLExt.join(settings.baseUrl, 'proxy', response.port.toString(), 'index.html');
      
    this.setState({
      instances: [...this.state.instances, url]
    });
    
    await showErrorMessage('Success', `Launched new trame instance on port ${response.port}`);
  }

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
          <Info label="Path" value={this.props.path} />
          
          <h4>
            Instances:
            <button className="launch-button" onClick={this.launchInstance} >Launch</button>
          </h4>
          <div className="instance-list">
            {this.state.instances.map((url) => (
              <TrameAppInstance
                name={this.props.name}
                path={this.props.path}
                url={url}
              />
            ))}
          </div>
        </Collapsible>
      </>
    );
  }
}


export class TrameSidepanelSegment extends React.Component<Record<string, never>,
  { apps: TrameAppOptions[] }> {
  constructor() {
    super({});
    this.state = { apps: [] };
    this.fetchData();
  }

  fetchData = async () => {
    this.setState({
      apps: await requestAPI<TrameAppOptions[]>('trame')
    });
  };

  render() {
    return (
      <>
        <h3>trame Apps:</h3>
        <div id="trame-instances" className="instance-list">
          {this.state.apps.map((app) => (
            <TrameApp
              name={app.displayName}
              path={app.path}
            />
          ))}
        </div>
      </>
    );
  }
}
