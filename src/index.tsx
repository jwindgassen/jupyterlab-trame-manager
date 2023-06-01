import {
  JupyterFrontEnd,
  JupyterFrontEndPlugin,
} from '@jupyterlab/application';
import { ReactWidget } from '@jupyterlab/apputils';
import { SplitPanel } from '@lumino/widgets';
import React from 'react';

import { ParaViewSidepanelSegment } from './paraview';
import { TrameSidepanelSegment } from './trame';

const plugin: JupyterFrontEndPlugin<void> = {
  id: 'juviz-extension',
  autoStart: true,
  activate: (app: JupyterFrontEnd) => {
    const panel = new SplitPanel();
    panel.orientation = 'vertical';
    panel.id = 'juviz-sidepanel';
    panel.title.iconClass = 'jp-ExtensionIcon jp-SideBar-tabIcon';
    panel.title.caption = 'JuWiz';

    // ParaView Segment
    const paraViewSegment = ReactWidget.create(<ParaViewSidepanelSegment />);
    paraViewSegment.addClass('juviz-sidepanel-segment');
    panel.addWidget(paraViewSegment);

    // trame Segment
    const trameSegment = ReactWidget.create(<TrameSidepanelSegment />);
    trameSegment.addClass('juviz-sidepanel-segment');
    panel.addWidget(trameSegment);

    app.shell.add(panel, 'left');
  },
};

export default plugin;
