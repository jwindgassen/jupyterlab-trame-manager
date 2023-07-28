import * as React from 'react';

export type Empty = Record<any, never>

export type InstanceList<T> = {
  instances: T[];
}

export class Info extends React.Component<{ label: string; value: string }> {
  render() {
    return (
      <div>
        <span style={{ fontWeight: 'bold' }}>{this.props.label}: </span>
        <span>{this.props.value}</span>
      </div>
    );
  }
}
