import Tooltips from "./_c/Tooltips";
import { Input } from "./ui/input";

type Props = {
  windowName: string;
  setWindowName: (newVal: string) => void;
};

export default function WindowName({ windowName, setWindowName }: Props) {
  return (
    <label htmlFor="window-name" className="w-fit mt-4">
      <div className="flex gap-2 items-center">
        <span className="text-xl">Window Name</span>
        <Tooltips>If you're using an emulator, set this to your emulator's window name (case-sensitive).</Tooltips>
      </div>
      <Input id="window-name" className="w-52" value={windowName} onChange={(e) => setWindowName(e.target.value)} />
    </label>
  );
}
