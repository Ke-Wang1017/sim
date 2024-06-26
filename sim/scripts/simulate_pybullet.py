import asyncio
from copy import deepcopy
import os
import time
import math
from typing import List, Dict

import numpy as np
from numpy.typing import NDArray
import pybullet as p
import pybullet_data

# local urdf is used for pybullet
URDF_LOCAL: str = "/home/kewang/sim/stompy/robot.urdf"

# starting positions for robot trunk relative to world frames
START_POS_TRUNK_PYBULLET: NDArray = np.array([0, 0, 1.2])
# START_EUL_TRUNK_PYBULLET: NDArray = np.array([-math.pi / 4, 0, 0])
START_EUL_TRUNK_PYBULLET: NDArray = np.array([-math.pi /2, 0, 0])

# starting joint positions (Q means "joint angles")
START_Q: Dict[str, float] = {
    # head (2dof)
    "joint_head_1_x4_1_dof_x4": -0.9425,
    "joint_head_1_x4_2_dof_x4": 0.0,
    # right leg (6dof)
    "joint_legs_1_x8_1_dof_x8": -0.50,
    "joint_legs_1_right_leg_1_x8_1_dof_x8": -0.50,
    "joint_legs_1_right_leg_1_x10_2_dof_x10": -0.2793,
    "joint_legs_1_right_leg_1_knee_revolute": 1.501,
    "joint_legs_1_right_leg_1_ankle_revolute": -0.6981,
    "joint_legs_1_right_leg_1_x4_1_dof_x4": 0.0,
    # left leg (6dof)
    "joint_legs_1_x8_2_dof_x8": 0.50,
    "joint_legs_1_left_leg_1_x8_1_dof_x8": -0.50,
    "joint_legs_1_left_leg_1_x10_1_dof_x10": 0.2793,
    "joint_legs_1_left_leg_1_knee_revolute": -1.501,
    "joint_legs_1_left_leg_1_ankle_revolute": 0.6981,
    "joint_legs_1_left_leg_1_x4_1_dof_x4": 0.0,
    # right arm (6dof)
    "joint_right_arm_1_x8_1_dof_x8": 1.57,
    "joint_right_arm_1_x8_2_dof_x8": 0.4363,
    "joint_right_arm_1_x6_1_dof_x6": 0.5236,
    "joint_right_arm_1_x6_2_dof_x6": 1.5708,
    "joint_right_arm_1_x4_1_dof_x4": 0,
    "joint_right_arm_1_hand_1_x4_1_dof_x4": -0.8727,
    # left arm (6dof)
    "joint_left_arm_2_x8_1_dof_x8": -1.57,
    "joint_left_arm_2_x8_2_dof_x8": -0.4363,
    "joint_left_arm_2_x6_1_dof_x6": -0.5236,
    "joint_left_arm_2_x6_2_dof_x6": -1.57,
    "joint_left_arm_2_x4_1_dof_x4": 0,
    "joint_left_arm_2_hand_1_x4_1_dof_x4": -0.8727,
    # right hand (2dof)
    "joint_right_arm_1_hand_1_slider_1": 0.0,
    "joint_right_arm_1_hand_1_slider_2": 0.0,
    # left hand (2dof)
    "joint_left_arm_2_hand_1_slider_1": 0.0,
    "joint_left_arm_2_hand_1_slider_2": 0.0,
}

# link names are based on the URDF
# EER means "end effector right"
# EEL means "end effector left"
EER_LINK: str = "link_right_arm_1_hand_1_x4_2_outer_1"
EEL_LINK: str = "link_left_arm_2_hand_1_x4_2_outer_1"

# kinematic chains for each arm and hand
EER_CHAIN_ARM: List[str] = [
    "joint_right_arm_1_x8_1_dof_x8",
    "joint_right_arm_1_x8_2_dof_x8",
    "joint_right_arm_1_x6_1_dof_x6",
    "joint_right_arm_1_x6_2_dof_x6",
    "joint_right_arm_1_x4_1_dof_x4",
    "joint_right_arm_1_hand_1_x4_1_dof_x4",
]
EEL_CHAIN_ARM: List[str] = [
    "joint_left_arm_2_x8_1_dof_x8",
    "joint_left_arm_2_x8_2_dof_x8",
    "joint_left_arm_2_x6_1_dof_x6",
    "joint_left_arm_2_x6_2_dof_x6",
    "joint_left_arm_2_x4_1_dof_x4",
    "joint_left_arm_2_hand_1_x4_1_dof_x4",
]
EER_CHAIN_HAND: List[str] = [
    "joint_right_arm_1_hand_1_slider_1",
    "joint_right_arm_1_hand_1_slider_2",
]
EEL_CHAIN_HAND: List[str] = [
    "joint_left_arm_2_hand_1_slider_1",
    "joint_left_arm_2_hand_1_slider_2",
]

# PyBullet IK will output a 37dof list in this exact order
IK_Q_LIST: List[str] = [
    "joint_head_1_x4_1_dof_x4",
    "joint_head_1_x4_2_dof_x4",
    "joint_right_arm_1_x8_1_dof_x8",
    "joint_right_arm_1_x8_2_dof_x8",
    "joint_right_arm_1_x6_1_dof_x6",
    "joint_right_arm_1_x6_2_dof_x6",
    "joint_right_arm_1_x4_1_dof_x4",
    "joint_right_arm_1_hand_1_x4_1_dof_x4",
    "joint_right_arm_1_hand_1_slider_1",
    "joint_right_arm_1_hand_1_slider_2",
    "joint_right_arm_1_hand_1_x4_2_dof_x4",
    "joint_left_arm_2_x8_1_dof_x8",
    "joint_left_arm_2_x8_2_dof_x8",
    "joint_left_arm_2_x6_1_dof_x6",
    "joint_left_arm_2_x6_2_dof_x6",
    "joint_left_arm_2_x4_1_dof_x4",
    "joint_left_arm_2_hand_1_x4_1_dof_x4",
    "joint_left_arm_2_hand_1_slider_1",
    "joint_left_arm_2_hand_1_slider_2",
    "joint_left_arm_2_hand_1_x4_2_dof_x4",
    "joint_torso_1_x8_1_dof_x8",
    "joint_legs_1_x8_1_dof_x8",
    "joint_legs_1_right_leg_1_x8_1_dof_x8",
    "joint_legs_1_right_leg_1_x10_2_dof_x10",
    "joint_legs_1_right_leg_1_knee_revolute",
    "joint_legs_1_right_leg_1_x10_1_dof_x10",
    "joint_legs_1_right_leg_1_ankle_revolute",
    "joint_legs_1_right_leg_1_x6_1_dof_x6",
    "joint_legs_1_right_leg_1_x4_1_dof_x4",
    "joint_legs_1_x8_2_dof_x8",
    "joint_legs_1_left_leg_1_x8_1_dof_x8",
    "joint_legs_1_left_leg_1_x10_1_dof_x10",
    "joint_legs_1_left_leg_1_knee_revolute",
    "joint_legs_1_left_leg_1_x10_2_dof_x10",
    "joint_legs_1_left_leg_1_ankle_revolute",
    "joint_legs_1_left_leg_1_x6_1_dof_x6",
    "joint_legs_1_left_leg_1_x4_1_dof_x4",
]


# PyBullet inverse kinematics (IK) params
# damping determines which joints are used for ik
# TODO: more custom damping will allow for legs/torso to help reach ee target
DAMPING_CHAIN: float = 0.1
DAMPING_NON_CHAIN: float = 10.0

# PyBullet init
HEADLESS: bool = True
if HEADLESS:
    print("Starting PyBullet in headless mode.")
    clid = p.connect(p.DIRECT)
else:
    print("Starting PyBullet in GUI mode.")
    p.connect(p.GUI)
p.setAdditionalSearchPath(pybullet_data.getDataPath())
robot = p.loadURDF(URDF_LOCAL, [0, 0, 0], useFixedBase=False)
plane = p.loadURDF("plane.urdf")
p.setGravity(0, 0, -9.8)
p.resetBasePositionAndOrientation(
    robot,
    START_POS_TRUNK_PYBULLET,
    p.getQuaternionFromEuler(START_EUL_TRUNK_PYBULLET),
)
pb_num_joints: int = p.getNumJoints(robot)
print(f"\t number of joints: {pb_num_joints}")
pb_joint_names: List[str] = [""] * pb_num_joints
pb_child_link_names: List[str] = [""] * pb_num_joints
pb_joint_upper_limit: List[float] = [0.0] * pb_num_joints
pb_joint_lower_limit: List[float] = [0.0] * pb_num_joints
pb_joint_ranges: List[float] = [0.0] * pb_num_joints
pb_start_q: List[float] = [0.0] * pb_num_joints
pb_damping: List[float] = [0.0] * pb_num_joints
pb_q_map: Dict[str, int] = {}

# global variables get updated by various async functions
q: Dict[str, float] = deepcopy(START_Q)

def ik(arm: str) -> None:
    start_time = time.time()
    if arm == "right":
        global goal_pos_eer, goal_orn_eer
        ee_id = pb_eer_id
        ee_chain = EER_CHAIN_ARM
        pos = goal_pos_eer
        orn = goal_orn_eer
    else:
        global goal_pos_eel, goal_orn_eel
        ee_id = pb_eel_id
        ee_chain = EEL_CHAIN_ARM
        pos = goal_pos_eel
        orn = goal_orn_eel
    # print(f"ik {arm} {pos} {orn}")
    pb_q = p.calculateInverseKinematics(
        robot,
        ee_id,
        pos,
        orn,
        pb_joint_lower_limit,
        pb_joint_upper_limit,
        pb_joint_ranges,
        pb_start_q,
    )
    global q
    for i, val in enumerate(pb_q):
        joint_name = IK_Q_LIST[i]
        if joint_name in ee_chain:
            q[joint_name] = val
            p.resetJointState(robot, pb_q_map[joint_name], val)
    print(f"ik {arm} took {time.time() - start_time} seconds")


for i in range(pb_num_joints):
    info = p.getJointInfo(robot, i)
    name = info[1].decode("utf-8")
    pb_joint_names[i] = name
    pb_child_link_names[i] = info[12].decode("utf-8")
    pb_joint_lower_limit[i] = info[9]
    pb_joint_upper_limit[i] = info[10]
    pb_joint_ranges[i] = abs(info[10] - info[9])
    if name in START_Q:
        pb_start_q[i] = START_Q[name]
    if name in EER_CHAIN_ARM or name in EEL_CHAIN_ARM:
        pb_damping[i] = DAMPING_CHAIN
    else:
        pb_damping[i] = DAMPING_NON_CHAIN
    if name in IK_Q_LIST:
        pb_q_map[name] = i
pb_eer_id = pb_child_link_names.index(EER_LINK)
pb_eel_id = pb_child_link_names.index(EEL_LINK)
for i in range(pb_num_joints):
    p.resetJointState(robot, i, pb_start_q[i])
print("\t ... done")
link_index = -1
for i in range(p.getNumJoints(robot)):
    info = p.getJointInfo(robot, i)
    print(info)
    if info[12].decode() == 'link_head_1_x4_1_pcb_1':
        link_index = i
        break
print('link index', link_index)
while True:
    # Step simulation
    p.stepSimulation()
    time.sleep(1./240.)


p.disconnect()



