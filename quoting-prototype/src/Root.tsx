import { Composition } from "remotion";
import { QuotingFlow } from "./scenes/QuotingFlow";
import { LifecycleFlow, LIFECYCLE_DURATION_FRAMES } from "./scenes/LifecycleFlow";
import { QuotingDetailFlow, QUOTING_DETAIL_DURATION_FRAMES } from "./scenes/QuotingDetailFlow";

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
      <Composition
        id="ProjectLifecycleFlow"
        component={LifecycleFlow}
        durationInFrames={LIFECYCLE_DURATION_FRAMES}
        fps={30}
        width={1440}
        height={900}
        defaultProps={{}}
      />
      <Composition
        id="QuotingDetailFlow"
        component={QuotingDetailFlow}
        durationInFrames={QUOTING_DETAIL_DURATION_FRAMES}
        fps={30}
        width={1440}
        height={900}
        defaultProps={{}}
      />
    </>
  );
};
