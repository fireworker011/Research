import { Caption } from "./Caption";
import { Stage } from "./Stage";

export const Frame: React.FC<{
  readonly tint: string;
  readonly caption: string;
  readonly children: React.ReactNode;
}> = ({ tint, caption, children }) => {
  return (
    <Stage tint={tint}>
      {children}
      <Caption text={caption} />
    </Stage>
  );
};
