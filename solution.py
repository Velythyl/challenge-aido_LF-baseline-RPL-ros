#!/usr/bin/env python3

import io
import os
import time

import numpy as np
import roslaunch
from PIL import Image
from rosagent import ROSAgent

from aido_schemas import protocol_agent, wrap_direct


class ROSTemplateAgent:
    def __init__(self, load_model=False, model_path=None):
        # Now, initialize the ROS stuff here:
        uuid = roslaunch.rlutil.get_or_generate_uuid(None, False)
        roslaunch.configure_logging(uuid)
        roslaunch_path = os.path.join(os.getcwd(), "template.launch")
        self.launch = roslaunch.parent.ROSLaunchParent(uuid, [roslaunch_path])
        self.launch.start()

        # Start the ROSAgent, which handles publishing images and subscribing to action
        self.agent = ROSAgent()

    def init(self, context, data):
        context.info("init()")

    def on_received_seed(self, context, data):
        np.random.seed(data)

    def on_received_episode_start(self, context, data):
        context.info("Starting episode %s." % data)

    def on_received_observations(self, context, data):
        jpg_data = data["camera"]["jpg_data"]
        obs = jpg2rgb(jpg_data)
        self.agent._publish_img(obs)
        self.agent._publish_info()

    def on_received_get_commands(self, context, data):
        while not self.agent.updated:
            time.sleep(0.01)

        pwm_left, pwm_right = self.agent.action
        self.agent.updated = False

        rgb = {"r": 0.5, "g": 0.5, "b": 0.5}
        commands = {
            "wheels": {"motor_left": pwm_left, "motor_right": pwm_right},
            "LEDS": {
                "center": rgb,
                "front_left": rgb,
                "front_right": rgb,
                "back_left": rgb,
                "back_right": rgb,
            },
        }

        context.write("commands", commands)

    def finish(self, context):
        context.info("finish()")


def jpg2rgb(image_data):
    """ Reads JPG bytes as RGB"""
    im = Image.open(io.BytesIO(image_data))
    im = im.convert("RGB")
    data = np.array(im)
    assert data.ndim == 3
    assert data.dtype == np.uint8
    return data


if __name__ == "__main__":
    agent = ROSTemplateAgent()
    wrap_direct(agent, protocol_agent)
