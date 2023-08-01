import * as React from 'react';
import Collapsible from 'react-collapsible';
import { showDialog, showErrorMessage } from '@jupyterlab/apputils';

import { requestAPI } from './handler';
import { ParaViewLauncherDialog } from './dialogs';
import { Info, Empty, InstanceList } from './components';


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
}


class ParaViewInstance extends React.Component<ParaViewInstanceOptions> {
  constructor(props: ParaViewInstanceOptions) {
    super(props);
  }

  render() {
    const label = (
      <>
        <b>{this.props.name}</b>
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
        </Collapsible>
      </>
    );
  }
}


export class ParaViewSidepanelSegment extends React.Component<Empty, InstanceList<ParaViewInstanceOptions>> {
  constructor() {
    super({});
    this.state = { instances: [] };
  }

  async componentDidMount() {
    await this.fetchData()
  }

  fetchData = async () => {
    this.setState({
      instances: await requestAPI<ParaViewInstanceOptions[]>('paraview')
    });
  };

  newInstance = async () => {
    const options = await showDialog({
      title: 'Launch a new ParaView instance',
      body: new ParaViewLauncherDialog()
    });
    console.log(options.value);

    const status = await requestAPI<ParaViewReturnStatus>('paraview', {
      method: 'POST',
      body: JSON.stringify(options.value)
    });

    await Promise.all([
      showErrorMessage(status.returnCode === 0 ? 'Success' : 'Error', status.message),
      this.fetchData(),
    ])
  };

  render() {
    return (
      <>
        <h3>
          Running ParaView backends:
          <button className='launch-button' onClick={this.newInstance}>Launch</button>
        </h3>
        <div id='paraview-instances' className='instance-list'>
          {this.state.instances.map((instance) => (
            <ParaViewInstance {...instance} />
          ))}
        </div>
      </>
    );
  }
}
