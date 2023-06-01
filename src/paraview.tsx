import * as React from 'react';
import Collapsible from 'react-collapsible';
import { showDialog } from '@jupyterlab/apputils';

import { requestAPI } from './handler';
import { ParaViewLauncherDialog } from './dialogs';
import { Info } from './components';

export enum ParaViewServerState {
  STARTING = 'Starting',
  RUNNING = 'Running',
  COMPLETING = 'Completing',
}

export type ParaViewOptions = {
  account: string;
  partition: string;
  nodes: number;
  runtime: string;
};

export type ParaViewInstanceOptions = ParaViewOptions & {
  state: ParaViewServerState;
  url: string;
};

class ParaViewInstance extends React.Component<ParaViewInstanceOptions> {
  constructor(props: ParaViewInstanceOptions) {
    super(props);
  }

  render() {
    const label = (
      <>
        <Info label='Nodes' value={this.props.nodes.toString()} />
        <Info label='Time' value={this.props.runtime} />
      </>
    );

    return (
      <>
        <Collapsible trigger={label}>
          <Info label='Allocation' value={this.props.state} />
          <Info label='Project' value={this.props.account} />
          <Info label='Partition' value={this.props.partition} />
          <Info label='Nodes' value={this.props.nodes.toString()} />
          <Info label='GPUs' value={(this.props.nodes * 4).toString()} />
          <Info label='Runtime' value={this.props.runtime} />
        </Collapsible>
      </>
    );
  }
}

export class ParaViewSidepanelSegment extends React.Component<Record<string, never>,
  { instaces: ParaViewInstanceOptions[] }> {
  constructor() {
    super({});
    this.state = { instaces: [] };

    this.fetchData();
  }

  fetchData = async () => {
    this.setState({
      instaces: await requestAPI<ParaViewInstanceOptions[]>('paraview')
    });
  };

  newInstance = async () => {
    const options = await showDialog({
      title: 'Launch a new ParaView instance',
      body: new ParaViewLauncherDialog()
    });
    console.log(options);
  };

  render() {
    return (
      <>
        <h3>Running ParaView backends:</h3>
        <div id='paraview-instances' className='instance-list'>
          {this.state.instaces.map((instance) => (
            <ParaViewInstance
              account={instance.account}
              partition={instance.partition}
              nodes={instance.nodes}
              runtime={instance.runtime}
              state={instance.state}
              url={instance.url}
            />
          ))}
        </div>
        <button onClick={this.newInstance}>Launch new Instance</button>
      </>
    );
  }
}
