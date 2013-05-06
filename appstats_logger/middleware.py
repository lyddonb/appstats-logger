#
# Copyright 2013 Robert Kluin
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
"""This is a simple middleware to handle setting up the App Stats recorder,
and then getting and dumping the profile data from it at the end of the
request.
"""
import json
import logging
import os

from google.appengine.ext.appstats.recording import recorder_proxy

from appstats_logger.recorder import Recorder


def stats_logger_wsgi_middleware(app):

    def appstats_wsgi_wrapper(environ, start_response):
        """Outer wrapper function around the WSGI protocol.

        The top-level appstats_wsgi_middleware() function returns this
        function to the caller instead of the app class or function passed
        in.  When the caller calls this function (which may happen
        multiple times, to handle multiple requests) this function
        instantiates the app class (or calls the app function), sandwiched
        between calls to start_recording() and end_recording() which
        manipulate the recording state.

        The signature is determined by the WSGI protocol.
        """
        # start: start_recording
        recorder_proxy.clear_for_current_request()
        env = environ
        if env is None:
            env = os.environ

        recorder_proxy.set_for_current_request(Recorder(env))
        # end: start_recording

        try:
            result = app(environ, start_response)
        except Exception:
            _emit_profile_data()
            raise

        if result is not None:
            for value in result:
                yield value

        _emit_profile_data()

    return appstats_wsgi_wrapper


def _emit_profile_data():
    """Get the current recorder and log the profiling data."""
    rec = recorder_proxy.get_for_current_request()
    logging.info("PROFILE: %s", json.dumps(rec.get_profile_data()))

    recorder_proxy.clear_for_current_request()
