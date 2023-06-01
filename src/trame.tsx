import * as React from 'react';
import Collapsible from 'react-collapsible';
import { Info } from './components';
import { requestAPI } from './handler';

type TrameAppOptions = {
  name: string;
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
      <>
        <Collapsible trigger="State: Running">
          <Info label="Connected To Backend" value={this.props.url} />
          <Info label="Root Directory" value={this.props.path} />
        </Collapsible>
        <button onClick={this.openInstance}>Open</button>
      </>
    );
  }
}

class TrameApp extends React.Component<TrameAppOptions> {
  constructor(props: TrameAppOptions) {
    super(props);
  }

  render() {
    const title = (
      <div>
        <b> {this.props.name} </b>
        <br />
        Running Instances: {this.props.instances.length}
      </div>
    );

    return (
      <>
        <Collapsible trigger={title}>
          <Info label="Path" value={this.props.path} />
          Instances:
          <div className="instance-list">
            {this.props.instances.map((url) => (
              <TrameAppInstance
                name={this.props.name}
                path={this.props.path}
                url={url}
              />
            ))}
          </div>
          <button
            style={{ background: 'green', color: 'white', margin: '10px' }}
          >
            Launch new instance
          </button>
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
              name={app.name}
              path={app.path}
              instances={app.instances}
            />
          ))}
        </div>
      </>
    );
  }
}
