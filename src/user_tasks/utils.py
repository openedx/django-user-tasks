"""
Utility functions for handling Celery task protocol compatibility.
"""

from celery import chain


def proto2_to_proto1(body, headers):
    """
    Convert a protocol v2 task body and headers to protocol v1 format.
    """
    args, kwargs, embed = body
    embedded = extract_proto2_embed(**embed)
    chained = embedded.pop("chain", None)
    new_body = dict(
        extract_proto2_headers(**headers),
        args=args,
        kwargs=kwargs,
        **embedded,
    )
    if chained:
        new_body["callbacks"].append(chain(chained))
    return new_body


def extract_proto2_headers(id, retries, eta, expires, group, timelimit, task, **_):  # pylint: disable=redefined-builtin
    """
    Extract relevant headers from protocol v2 format.
    """
    return {
        "id": id,
        "task": task,
        "retries": retries,
        "eta": eta,
        "expires": expires,
        "utc": True,
        "taskset": group,
        "timelimit": timelimit,
    }


def extract_proto2_embed(callbacks=None, errbacks=None, task_chain=None, chord=None, **_):
    """
    Extract embedded task metadata.
    """
    return {
        "callbacks": callbacks or [],
        "errbacks": errbacks or [],
        "chain": task_chain,
        "chord": chord,
    }
