import { Input } from "@movu/ui";

interface FieldProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label: string;
  helper?: string;
}

export function Field({ label, helper, id, ...props }: FieldProps) {
  const inputId = id ?? label.toLowerCase().replace(/\s+/g, "-");
  return (
    <label className="field" htmlFor={inputId}>
      <span>{label}</span>
      <Input id={inputId} {...props} />
      {helper && <small>{helper}</small>}
    </label>
  );
}
