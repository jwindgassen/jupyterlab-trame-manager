import { Dialog } from '@jupyterlab/apputils';
import { Widget } from '@lumino/widgets';

import { ParaViewLaunchOptions } from './paraview';
import { TrameLaunchOptions } from './trame';
import { requestAPI } from './handler';

type UserData = {
  user: string;
  home: string;
  accounts: string[];
  partitions: string[];
};

function createLabel(forAttribute: string, textContent: string) {
  const label = document.createElement('label');
  label.htmlFor = forAttribute;
  label.textContent = textContent;
  return label;
}

function createSelect(id: string, options: string[]) {
  const select = document.createElement('select');
  select.id = id;

  for (const option of options) {
    const optionElement = document.createElement('option');
    optionElement.value = option;
    optionElement.textContent = option;
    select.appendChild(optionElement);
  }

  return select;
}

function createInput(
  id: string,
  type: string,
  value: string,
  attributes: [string, string][] = []
) {
  const input = document.createElement('input');
  input.type = type;
  input.id = id;
  input.value = value;

  input.classList.add('form-input');

  for (const [option, value] of attributes) {
    input.setAttribute(option, value);
  }

  return input;
}

export class ParaViewLauncherDialog
  extends Widget
  implements Dialog.IBodyWidget<ParaViewLaunchOptions>
{
  private readonly _nameElement: HTMLInputElement;
  private readonly _accountElement: HTMLSelectElement;
  private readonly _partitionElement: HTMLSelectElement;
  private readonly _nodesElement: HTMLInputElement;
  private readonly _timeElement: HTMLInputElement;

  constructor() {
    super();

    // Name form
    const nameForm = document.createElement('div');
    nameForm.appendChild(createLabel('name', 'Name: '));
    nameForm.appendChild(
      (this._nameElement = createInput('name', 'text', 'ParaView Server'))
    );
    this.node.appendChild(nameForm);

    // Account form
    const accountForm = document.createElement('div');
    accountForm.appendChild(createLabel('account', 'Account: '));
    accountForm.appendChild(
      (this._accountElement = createSelect('account', []))
    );
    this.node.appendChild(accountForm);

    // Partition form
    const partitionForm = document.createElement('div');
    partitionForm.appendChild(createLabel('partition', 'Partition: '));
    partitionForm.appendChild(
      (this._partitionElement = createSelect('partition', []))
    );
    this.node.appendChild(partitionForm);

    // Nodes form
    const nodesForm = document.createElement('div');
    nodesForm.appendChild(createLabel('nodes', 'Nodes: '));
    nodesForm.appendChild(
      (this._nodesElement = createInput('nodes', 'number', '4', [
        ['min', '1'],
        ['max', '32'],
        ['step', '1']
      ]))
    );
    this.node.appendChild(nodesForm);

    // Time form
    const timeForm = document.createElement('div');
    timeForm.appendChild(createLabel('time', 'Time: '));
    timeForm.appendChild(
      (this._timeElement = createInput('time', 'text', '02:00:00'))
    );
    this.node.appendChild(timeForm);

    this.fetchUserData();
  }

  fetchUserData = async () => {
    const data = await requestAPI<UserData>('user');

    for (const account of data.accounts) {
      const optionElement = document.createElement('option');
      optionElement.value = account;
      optionElement.textContent = account;
      this._accountElement.appendChild(optionElement);
    }

    for (const partition of data.partitions) {
      const optionElement = document.createElement('option');
      optionElement.value = partition;
      optionElement.textContent = partition;
      this._partitionElement.appendChild(optionElement);
    }
  };

  getValue(): ParaViewLaunchOptions {
    return {
      name: this._nameElement.value,
      account: this._accountElement.value,
      partition: this._partitionElement.value,
      nodes: Number(this._nodesElement.value),
      timeLimit: this._timeElement.value
    };
  }
}

export class TrameLauncherDialog
  extends Widget
  implements Dialog.IBodyWidget<TrameLaunchOptions>
{
  private readonly _nameElement: HTMLInputElement;
  private readonly _dataDirElement: HTMLInputElement;

  constructor(appName: string, instances: number) {
    super();

    // Name form
    const nameForm = document.createElement('div');
    nameForm.appendChild(createLabel('name', 'Name: '));
    nameForm.appendChild(
      (this._nameElement = createInput(
        'name',
        'text',
        `${appName} Instance ${instances + 1}`
      ))
    );
    this.node.appendChild(nameForm);

    // Data Directory form
    const dataDirForm = document.createElement('div');
    dataDirForm.appendChild(createLabel('dataDir', 'Data Directory: '));
    dataDirForm.appendChild(
      (this._dataDirElement = createInput('dataDir', 'text', ''))
    );
    this.node.appendChild(dataDirForm);

    this.fetchUserData();
  }

  fetchUserData = async () => {
    const data = await requestAPI<UserData>('user');
    this._dataDirElement.value = data.home;
  };

  getValue(): TrameLaunchOptions {
    return {
      name: this._nameElement.value,
      dataDirectory: this._dataDirElement.value
    };
  }
}
