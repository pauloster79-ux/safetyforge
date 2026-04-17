import { Composition } from "remotion";
import { QuotingFlow } from "./scenes/QuotingFlow";

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="JakeQuotingFlow"
        component={QuotingFlow}
        durationInFrames={30 * 85} // 85 seconds at 30fps
        fps={30}
        width={1440}
        height={900}
        defaultProps={{}}
      />
    </>
  );
};
