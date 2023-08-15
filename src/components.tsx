import * as React from 'react';


export function Info(props: { label: string; value: string }) {
  return (
    <div>
      <span style={{ fontWeight: 'bold' }}>{props.label}: </span>
      <span>{props.value}</span>
    </div>
  );
}