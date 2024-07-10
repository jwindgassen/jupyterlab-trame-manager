import {
  ILayoutRestorer,
  JupyterFrontEnd,
  JupyterFrontEndPlugin
} from '@jupyterlab/application';
import { ReactWidget } from '@jupyterlab/apputils';
import { SplitPanel } from '@lumino/widgets';
import React from 'react';

import ParaViewSidepanelSegment from './paraview';
import TrameSidepanelSegment from './trame';
import { trameIcon } from './icons';
import { commandRegistryInstance } from './components';

const plugin: JupyterFrontEndPlugin<void> = {
  id: 'jupyterlab-trame-manager',
  autoStart: true,
  requires: [ILayoutRestorer],
  activate: (app: JupyterFrontEnd, restorer: ILayoutRestorer | null) => {
    commandRegistryInstance.instance = app.commands;

    const panel = new SplitPanel();
    panel.orientation = 'vertical';
    panel.id = 'trame-manager-sidepanel';
    panel.title.icon = trameIcon;
    panel.title.caption = 'trame Manager';

    // ParaView Segment
    const paraViewSegment = ReactWidget.create(<ParaViewSidepanelSegment />);
    paraViewSegment.addClass('trame-manager-sidepanel-segment');
    panel.addWidget(paraViewSegment);

    // trame Segment
    const trameSegment = ReactWidget.create(<TrameSidepanelSegment />);
    trameSegment.addClass('trame-manager-sidepanel-segment');
    panel.addWidget(trameSegment);

    if (restorer) {
      restorer.add(panel, 'jupyterlab-trame-manager:sidebar');
    }

    app.shell.add(panel, 'left');
  }
};

export default plugin;
