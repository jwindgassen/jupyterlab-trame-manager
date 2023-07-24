import * as React from 'react';
import Collapsible from 'react-collapsible';
import { showDialog } from '@jupyterlab/apputils';

import { requestAPI } from './handler';
import { ParaViewLauncherDialog } from './dialogs';
import { Info } from './components';


export type ParaViewLaunchOptions = {
  account: string;
  partition: string;
  nodes: number;
  timeLimit: string;
};

export type ParaViewInstanceOptions = ParaViewLaunchOptions & {
  state: string;
  timeUsed: string;
  url?: string;
};


class ParaViewInstance extends React.Component<ParaViewInstanceOptions> {
  constructor(props: ParaViewInstanceOptions) {
    super(props);
  }

  render() {
    const label = (
      <>
        <Info label='Nodes' value={this.props.nodes.toString()} />
        <Info label='Status' value={this.props.state} />
        <Info label='Time' value={`${this.props.timeUsed} / ${this.props.timeLimit}`} />
      </>
    );

    return (
      <>
        <Collapsible trigger={label}>
          <Info label='Project' value={this.props.account} />
          <Info label='Partition' value={this.props.partition} />
          <Info label='Nodes' value={this.props.nodes.toString()} />
          <Info label='Port for Connection' value={this.props.url ?? ''} />
        </Collapsible>
      </>
    );
  }
}


export class ParaViewSidepanelSegment extends React.Component<Record<string, never>, { instaces: ParaViewInstanceOptions[] }> {
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
    console.log(options.value);
    
    await requestAPI<Record<string, never>>('paraview', {
        method: 'POST',
        body: JSON.stringify(options.value)
    })
    await this.fetchData();
  };

  render() {
    return (
      <>
        <h3>
          Running ParaView backends:
          <button className='launch-button' onClick={this.newInstance} >Launch</button>
        </h3>
        <div id='paraview-instances' className='instance-list'>
          {this.state.instaces.map((instance) => (
            <ParaViewInstance {...instance} />
          ))}
        </div>
      </>
    );
  }
}
