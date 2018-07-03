# -*- coding: utf-8 -*-

import pika
from restapi.flask_ext import BaseExtension, get_logger
# from utilities.logs import re_obscure_pattern

log = get_logger(__name__)

'''
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
        from restapi.confs import PRODUCTION
        if not PRODUCTION:
            log.warning("Skipping Rabbit")
            # TODO: Have a TEST setting for testbeds, with different queue?
            # TODO: Log into some file if Rabbit not available?

            class Empty:
                pass
            return Empty()

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
        conn_wrapper = RabbitWrapper(variables)

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

    def __init__(self, variables):
        self.__variables = variables
        self.__connection = connection
        self.__channel = channel

    def connect(self):
        variables = self.__variables
        credentials = pika.PlainCredentials(
            variables.get('user'),
            variables.get('password')
        )
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host=variables.get('host'),
                port=int(variables.get('port')),
                virtual_host=variables.get('vhost'),
                credentials=credentials,
                heartbeat_interval=variables.get('heartbeat_interval')
            )
        )
        self.__connection = connection

    '''
    Return existing channel (if healthy) or create and
    return new one.
    This is the method supposed to be used by any
    outside client that wants to interact with RabbitMQ.
    '''
    def channel(self):
        if self.__channel is None or self.__channel.is_closed or self.__channel.is_closing:
            self.__channel = self._get_new_channel() 
        return self.__channel

    '''
    Create a new channel. If there is no connection,
    it will try to connect.
    '''
    def _get_new_channel(self):
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
        if self.__connection.is_closed or self.__connection.is_closing:
            log.debug('Connection already closed or closing.')
        else:
            self.__connection.close()
