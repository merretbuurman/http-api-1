# -*- coding: utf-8 -*-

import pika
from restapi.flask_ext import BaseExtension, get_logger
# from utilities.logs import re_obscure_pattern

log = get_logger(__name__)

'''
This class provides a RabbitMQ connection 
in order to write log messages into a queue.

This is used in SeaDataCloud, where the log
queues are then consumed by Logstash / ElasticSearch.

Note:
When adding a heartbeat interval, please make sure 
that the value is higher than whichever long-running 
task that happens in the same thread.

Heartbeats are not sent/received while a thread is
blocked, so that results in error. More info:

 * https://stackoverflow.com/questions/15015714/a-good-heartbeat-interval-for-pika-rabbitmq-in-amazon-ec2
 * https://stackoverflow.com/questions/14572020/handling-long-running-tasks-in-pika-rabbitmq

'''
class RabbitExt(BaseExtension):

    def custom_connection(self, **kwargs):

        #############################
        # NOTE: for SeaDataCloud
        # Unused for debugging at the moment
        dont_connect = False
        from restapi.confs import PRODUCTION
        if not PRODUCTION:
            log.warning("Skipping Rabbit, logging to normal log instead.")
            dont_connect = True
            # TODO: Have a TEST setting for testbeds, with different queue?

        #############################
        variables = self.variables
        # print("\n\n\nTEST")

        # DIRECT AMQP connection
        # uri = 'amqp://%s:%s@%s:%s/' % (
        #     variables.get('user'),
        #     variables.get('password'),
        #     variables.get('host'),
        #     variables.get('port'),
        # ) + '%' + '2F'
        # log.very_verbose("URI IS %s" % re_obscure_pattern(uri))
        # parameter = pika.connection.URLParameters(uri)
        # return pika.BlockingConnection(parameter)

        # PIKA based
        conn_wrapper = RabbitWrapper(variables, dont_connect)

        # channel = connection.channel()
        # # Declare exchange, queue, and binding
        # channel.queue_declare(queue=QUEUE)
        # channel.exchange_declare(exchange=EXCHANGE, exchange_type='topic')
        # channel.queue_bind(
        #     exchange=EXCHANGE, queue=QUEUE, routing_key=ROUTING_KEY)
        return conn_wrapper

    # def custom_init(self, pinit=False, pdestroy=False, **kwargs):
    #     """ Note: we ignore args here """

    #     # recover instance with the parent method
    #     queue = super().custom_init()
    #     print(queue)
    #     return queue

class RabbitWrapper(object):

    def __init__(self, variables, dont_connect=False):
        self.__variables = variables
        self.__connection = connection
        self.__channel = channel
        self.__dont_connect = dont_connect
        # TODO: Declare queue and exchange, just in case?

        # Initial connection:
        self.connect()

    '''
    Connect to RabbitMQ, unless the dont-connect parameter
    is set.
    '''
    def connect(self):
        if self.__dont_connect:
            return
        variables = self.__variables
        credentials = pika.PlainCredentials(
            variables.get('user'),
            variables.get('password')
        )
        try:
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(
                    host=variables.get('host'),
                    port=int(variables.get('port')),
                    virtual_host=variables.get('vhost'),
                    credentials=credentials,
                    heartbeat_interval=variables.get('heartbeat_interval')
                )
            )
            log.debug('Connecting to the Rabbit')
            self.__connection = connection

        except pika.exceptions.ConnectionClosed as e:
            log.warn('Could not connect to RabbitMQ. Log messages will be written into file instead.')
            self.__dont_connect = True
            self.__connection = None

    '''
    Send a log message to the RabbitMQ queue, unless
    the dont-connect parameter is set. In that case,
    the messages get logged into the normal log files.
    If the connection is dead, reconnection is attempted.
    '''
    def log_json_to_queue(self, dictionary_message, app_name, exchange, queue):
        body = json.dumps(dictionary_message)

        if self.__dont_connect:
            log.info('RABBIT LOG MESSAGE (%s, %s, %s): %s' % (app_name, exchange, queue, body))
            return

        filter_code = 'de.dkrz.seadata.filter_code.json'
        permanent_delivery=2
        props = pika.BasicProperties(
            delivery_mode=permanent_delivery,
            headers={'app_name': app_name, 'filter_code': filter_code},
        )

        max_publish = 3
        for i in xrange(max_publish):
            try:
                channel = self.channel()
                channel.basic_publish(
                    exchange=exchange,
                    routing_key=queue,
                    properties=props,
                    body=body,
                )
                log.verbose('Succeeded to send message to RabbitMQ in try (%s/%s)' % ((i+1), max_publish))
                break
            except pika.exceptions.ConnectionClosed:
               log.verbose('Failed to send log message in try (%s/%s), because connection is dead.' % ((i+1), max_publish))
                self.connect()
            except pika.exceptions.ChannelClosed:
               log.verbose('Failed to send log message in try (%s/%s), because channel is dead.' % ((i+1), max_publish))
                self.channel()


    '''
    Return existing channel (if healthy) or create and
    return new one.
    This is the method supposed to be used by any
    outside client that wants to interact with RabbitMQ.
    '''
    def channel(self):
        if self.__dont_connect:
            return None
        if self.__channel is None or self.__channel.is_closed or self.__channel.is_closing:
            self.__channel = self._get_new_channel() 
        return self.__channel

    '''
    Create a new channel. If there is no connection,
    it will try to connect.
    '''
    def _get_new_channel(self):
        if self.__dont_connect:
            return None
        if self.__connection is None:
            log.warning('Can not get new channel if connection is closed. Reconnecting.')
            self.connect()
        log.debug('Creating new channel.')
        return self.__connection.channel()

    '''
    Cleanly close the connection.
    '''
    def close_connection(self):
        # TODO: This must be called!
        if self.__dont_connect:
            return
        if self.__connection.is_closed or self.__connection.is_closing:
            log.debug('Connection already closed or closing.')
        else:
            self.__connection.close()
