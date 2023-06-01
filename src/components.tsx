import * as React from 'react';

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
