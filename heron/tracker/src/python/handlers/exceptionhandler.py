import tornado.gen
import tornado.web

from heron.tracker.src.python import constants
from heron.tracker.src.python.handlers import BaseHandler
from heron.tracker.src.python.log import Log as LOG

from heron.proto import common_pb2
from heron.proto import tmaster_pb2

class ExceptionHandler(BaseHandler):
  """
  URL - /topologies/exceptions?dc=<dc>&topology=<topology> \
        &environ=<environment>&component=<component>
  Parameters:
   - dc - Name of dc.
   - environ - Running environment.
   - topology - Name of topology (Note: Case sensitive. Can only
                include [a-zA-Z0-9-_]+)
   - component - Component name
   - instance - (optional, repeated)

  Returns all exceptions for the component of the topology.
  """
  def initialize(self, tracker):
    self.tracker = tracker

  @tornado.gen.coroutine
  def get(self):
    try:
      dc = self.get_argument_dc()
      environ = self.get_argument_environ()
      topName = self.get_argument_topology()
      component = self.get_argument_component()
      topology = self.tracker.getTopologyByDcEnvironAndName(dc, environ, topName)
      instances = self.get_arguments(constants.PARAM_INSTANCE)
      exceptions_logs = yield tornado.gen.Task(self.getComponentException,
                                               topology.tmaster, component, instances)
      self.write_success_response(exceptions_logs)
    except Exception as e:
      self.write_error_response(e)

  @tornado.gen.coroutine
  def getComponentException(self, tmaster, component_name, instances=[], callback=None):
    """
    Get all (last 1000) exceptions for 'component_name' of the topology.
    Returns an Array of exception logs on success.
    Returns json with message on failure.
    """
    if not tmaster or not tmaster.host or not tmaster.stats_port:
      return

    exception_request = tmaster_pb2.ExceptionLogRequest()
    exception_request.component_name = component_name
    if len(instances) > 0:
      exception_request.instances.extend(instances)
    request_str = exception_request.SerializeToString()
    port = str(tmaster.stats_port)
    host = tmaster.host
    url = "http://{0}:{1}/exceptions".format(host, port)
    request = tornado.httpclient.HTTPRequest(url,
                                             body=request_str,
                                             method='POST',
                                             request_timeout=5)
    LOG.debug('Making HTTP call to fetch exceptions url: %s' % url)
    try:
      client = tornado.httpclient.AsyncHTTPClient()
      result = yield client.fetch(request)
      LOG.debug("HTTP call complete.")
    except tornado.httpclient.HTTPError as e:
      raise Exception(str(e))


    # Check the response code - error if it is in 400s or 500s
    responseCode = result.code
    print responseCode
    if responseCode >= 400:
      message = "Error in getting exceptions from Tmaster, code: " + responseCode
      LOG.error(message)
      raise tornado.gen.Return({
        "message": message
      })

    # Parse the response from tmaster.
    exception_response = tmaster_pb2.ExceptionLogResponse()
    exception_response.ParseFromString(result.body)

    if exception_response.status.status == common_pb2.NOTOK:
      if exception_response.status.HasField("message"):
        raise tornado.gen.Return({
          "message": exception_response.status.message
        })

    # Send response
    ret = []
    for exception_log in exception_response.exceptions:
      ret.append({'hostname': exception_log.hostname,
                  'instance_id': exception_log.instance_id,
                  'stack_trace': exception_log.stacktrace,
                  'lasttime': exception_log.lasttime,
                  'firsttime': exception_log.firsttime,
                  'count': str(exception_log.count),
                  'logging': exception_log.logging})
    raise tornado.gen.Return(ret)
