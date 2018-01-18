'''
Utilities
'''

import tensorflow as tf
from gym.utils import play

import gym
import pygame
import sys
import time
import matplotlib
import numpy as np
from numpy.random import uniform

try:
    matplotlib.use('GTK3Agg')
    import matplotlib.pyplot as plt
except Exception:
    pass

from collections import deque
from pygame.locals import HWSURFACE, DOUBLEBUF, RESIZABLE, VIDEORESIZE


def variable_summaries(var, collections):
    '''
    Saves metrics about a variable
    :param var:
    :return:
    '''
    with tf.name_scope('summaries'):
        mean = tf.reduce_mean(var)
        tf.summary.scalar('mean', mean, collections='Variables')

    with tf.name_scope('stddev'):
        stddev = tf.sqrt(tf.reduce_mean(tf.square(var - mean)))

    tf.summary.scalar('stddev', stddev, collections=collections)
    tf.summary.scalar('max', tf.reduce_max(var), collections=collections)
    tf.summary.scalar('min', tf.reduce_min(var), collections=collections)
    tf.summary.histogram('histogram', var, collections=collections)


def Fetch_trajectories(agent, beta=1, humans=True):

    if humans:
        play_expert_agent_humans(agent.env, agent.policy, agent.data_path, beta)


def save_state(previous_states, action, save_path):
    '''
    saves staes
    :param previous_states: (np array) current image and 3 previous one
    :param action: (np array) action chosen by the expert
    :param save_path: (str)
    '''

    with open('{}/states_list.txt', 'w') as file:
        lines = file.readlines()

    state_number = int(lines[len(lines)][-1])+1
    np.save('{}/images/{}'.format(save_path, state_number), previous_states)
    np.save('{}/actions/{}'.format(save_path, state_number), action)


def play_expert_agent_humans(env, agent_policy, data_set_path, beta, transpose=True, fps=130, zoom=5, callback=None,
                             keys_to_action=None):
    '''
    This function is an adaptation of the gym.utils.play function that allows the agent to play in place of the expert,
    and to save the states.
    :param env: (gym.Env)
    :param agent_policy: (network.predict)
    :param data_set_path: (str)
    :param proba: (float) proba to fetch expert
    :param transpose: (Boolean) If True the output of observation is transposed.
    :param fps: (int) frames per seconds
    :param zoom: (float) Make screen edge this many times bigger
    :param callback: here we use callback to save the trajectory
    :param keys_to_action: (dict)
            {
                # ...
                sorted(ord('w'), ord(' ')) -> 2
                # ...
            }
    '''

    obs_s = env.observation_space
    assert type(obs_s) == gym.spaces.box.Box
    assert len(obs_s.shape) == 2 or (len(obs_s.shape) == 3 and obs_s.shape[2] in [1, 3])

    if keys_to_action is None:
        if hasattr(env, 'get_keys_to_action'):
            keys_to_action = env.get_keys_to_action()

        elif hasattr(env.unwrapped, 'get_keys_to_action'):
            keys_to_action = env.unwrapped.get_keys_to_action()

        else:
            assert False, env.spec.id + " does not have explicit key to action mapping, " + \
                          "please specify one manually"
    relevant_keys = set(sum(map(list, keys_to_action.keys()), []))

    if transpose:
        video_size = env.observation_space.shape[1], env.observation_space.shape[0]

    else:
        video_size = env.observation_space.shape[0], env.observation_space.shape[1]

    if zoom is not None:
        video_size = int(video_size[0] * zoom), int(video_size[1] * zoom)

    pressed_keys = []
    running = True
    env_done = True

    screen = pygame.display.set_mode(video_size)
    clock = pygame.time.Clock()

    while running:
        if env_done:
            env_done = False
            obs = env.reset()
            previous_obs = np.stack([obs for _ in range(4)])

        else:
            u = uniform()
            if u < beta:
                action = keys_to_action[tuple(sorted(pressed_keys))]

            else:
                action = agent_policy(previous_obs)
                obs, rew, env_done, info = env.step(action)
                action = keys_to_action[tuple(sorted(pressed_keys))]


            previous_obs[3, :, :, :] = previous_obs[2, :, :, :]
            previous_obs[2, :, :, :] = previous_obs[1, :, :, :]
            previous_obs[1, :, :, :] = previous_obs[0, :, :, :]
            previous_obs[0, :, :, :] = obs

            if callback is not None:
                callback(previous_obs, action, data_set_path)

        if obs is not None:
            if len(obs.shape) == 2:
                obs = obs[:, :, None]

            if obs.shape[2] == 1:
                obs = obs.repeat(3, axis=2)

            display_arr(screen, obs, transpose=transpose, video_size=video_size)

        # process pygame events
        for event in pygame.event.get():
            # test events, set key states
            if event.type == pygame.KEYDOWN:
                if event.key in relevant_keys:
                    pressed_keys.append(event.key)
                elif event.key == 27:
                    running = False
            elif event.type == pygame.KEYUP:
                if event.key in relevant_keys:
                    pressed_keys.remove(event.key)
            elif event.type == pygame.QUIT:
                running = False
            elif event.type == VIDEORESIZE:
                video_size = event.size
                screen = pygame.display.set_mode(video_size)
                print(video_size)

        pygame.display.flip()
        clock.tick(fps)
    pygame.quit()


def display_arr(screen, arr, video_size, transpose):
    arr_min, arr_max = arr.min(), arr.max()
    arr = 255.0 * (arr - arr_min) / (arr_max - arr_min)
    pyg_img = pygame.surfarray.make_surface(arr.swapaxes(0, 1) if transpose else arr)
    pyg_img = pygame.transform.scale(pyg_img, video_size)
    screen.blit(pyg_img, (0, 0))



if __name__ == "__main__":
    from Utils import Fetch_trajectories
    from agent import Agent
    agent = Agent("pong", "/Users/charlesdognin/Desktop/Imitation_Learning/pong", 0)
    Fetch_trajectories(agent, beta=1)