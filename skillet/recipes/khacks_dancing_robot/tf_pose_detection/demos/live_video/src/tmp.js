async function poseKeypointsToPoseClass(poses) {
  console.log(poses);

  const pose = poses?.[0];
  if (!pose) {
    console.log("No pose detected");
    return;
  }

  const keypoints = pose?.keypoints;
  if (!keypoints) {
    console.log("No pose keypoints detected");
    return;
  }

  // COCO Keypoints: Used in MoveNet
  // ["nose", "left_eye", "right_eye", "left_ear", "right_ear"]
  const HEAD_POINTS = Object.freeze([0, 1, 2, 3, 4]);
  // ["left_shoulder", "right_shoulder", "left_elbow", "right_elbow", "left_wrist", "right_wrist"]
  const ARM_POINTS = Object.freeze([7, 8, 9, 10]);
  // ["left_shoulder", "right_shoulder"]
  const SHOULDER_POINTS = Object.freeze([5, 6]);
  // ["left_hip", "right_hip"]
  const HIP_POINTS = Object.freeze([11, 12]);

  // Find Avg Head height
  let [avgHeadY, sumHeadY, numHeadPts] = [0, 0, 0];
  HEAD_POINTS.forEach((headPoint) => {
    const headPt = keypoints?.[headPoint];
    if (headPt) {
      sumHeadY += headPt.y;
      numHeadPts += 1;
    }
  });

  // Find Avg shoulder height
  let [avgShoulderY, sumShoulderY, numShoulderPts] = [0, 0, 0];
  SHOULDER_POINTS.forEach((shoulderPoint) => {
    const shoulderPt = keypoints?.[shoulderPoint];
    if (shoulderPt) {
      sumShoulderY += shoulderPt.y;
      numShoulderPts += 1;
    }
  });

  // Find Avg neck height

  // Find Avg Arm height
  let [avgArmY, sumArmY, numArmPts] = [0, 0, 0];
  ARM_POINTS.forEach((ArmPoint) => {
    const ArmPt = keypoints?.[ArmPoint];
    if (ArmPt) {
      sumArmY += ArmPt.y;
      numArmPts += 1;
    }
  });

  // Find Avg hip height
  const SCORE_MIN_THRESHOLD = 0.1;
  let [avgHipY, sumHipY, numHipPts] = [0, 0, 0];
  HIP_POINTS.forEach((hipPoint) => {
    const hipPt = keypoints?.[hipPoint];
    if (hipPt && hipPt?.score > SCORE_MIN_THRESHOLD) {
      // console.log(hipPt?.score)
      sumHipY += hipPt.y;
      numHipPts += 1;
    }
  });

  // console.log(`numHeadPts: ${numHeadPts}`);
  // console.log(`numArmPts: ${numArmPts}`);
  // console.log(`numHipPts: ${numHipPts}`);

  let warningMsg = "Show missing ";
  if (!numHeadPts || !numArmPts || !numShoulderPts || !numHipPts) {
    if (!numHeadPts) warningMsg += "Head ";
    if (!numArmPts) warningMsg += "Arms ";
    if (!numShoulderPts) warningMsg += "Shoulders ";
    if (!numHipPts) warningMsg += "Hip ";
    console.log(`%c ${warningMsg}`, "font-size: 12px; font-weight: bold");
  } else {
    avgHeadY = sumHeadY / numHeadPts;
    avgArmY = sumArmY / numArmPts;
    avgShoulderY = sumShoulderY / numShoulderPts;
    avgHipY = sumHipY / numHipPts;

    const avgNeckY = (avgHeadY + avgShoulderY) / 2;
    const avgChestY = (avgShoulderY + avgHipY) / 2;

    // console.log(`avgArmY: ${avgArmY}`)
    // console.log(`avgNeckY: ${avgNeckY}`)
    // console.log(`avgChestY: ${avgChestY}`)

    const poseType = Object.seal({ name: "Unk", color: "None" });
    if (avgArmY < avgNeckY) {
      poseType.name = "Y";
      poseType.color = "red";
    } else if (avgChestY < avgArmY) {
      poseType.name = "A";
      poseType.color = "cyan";
    } else {
      poseType.name = "T";
      poseType.color = "green";
    }

    console.log(
      `%c ${poseType.name}`,
      `font-size: 72px; font-weight: bold; color: ${poseType.color}`
    );

    const curPose = poseType.name;
    if (prevPose !== curPose) {
      try {
        if (!locked) {
          locked = true;
          const API = "http://127.0.0.1:5000";
          const trajectory = `${prevPose}_POSE_TO_${curPose}_POSE`;
          console.log(
            `%c ${prevPose} -> ${curPose}`,
            "font-size: 72px; font-weight: bold; color: yellow"
          );
          const res = await fetch(`${API}/send_trajectory/${trajectory}`);
          const response = await res.json();
          console.log(response);
          prevPose = curPose;
          locked = false;
        }
      } catch (error) {
        //console.error(error);
      } finally {
        //prevPose = poseType.name;
      }
    }
  }
}
