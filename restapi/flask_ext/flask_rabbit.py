# -*- coding: utf-8 -*-

import pika
from restapi.flask_ext import BaseExtension, get_logger
# from utilities.logs import re_obscure_pattern

log = get_logger(__name__)


class RabbitExt(BaseExtension):

    def custom_connection(self, **kwargs):

        #############################
        # NOTE: for SeaDataCloud
        # Unused for debugging at the moment
        # from restapi.confs import PRODUCTION
        # if not PRODUCTION:
        if True:
            log.warning("Skipping Rabbit")

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
        credentials = pika.PlainCredentials(
            variables.get('user'),
            variables.get('password')
        )
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host=variables.get('host'),
                port=int(variables.get('port')),
                virtual_host=variables.get('vhost'),
                credentials=credentials
            )
        )
        log.debug('Connecting to the Rabbit')

        # channel = connection.channel()
        # # Declare exchange, queue, and binding
        # channel.queue_declare(queue=QUEUE)
        # channel.exchange_declare(exchange=EXCHANGE, exchange_type='topic')
        # channel.queue_bind(
        #     exchange=EXCHANGE, queue=QUEUE, routing_key=ROUTING_KEY)
        return connection

    # def custom_init(self, pinit=False, pdestroy=False, **kwargs):
    #     """ Note: we ignore args here """

    #     # recover instance with the parent method
    #     queue = super().custom_init()
    #     print(queue)
    #     return queue
<<<<<<< Updated upstream
=======

class RabbitWrapper(object):

    def __init__(self, variables, dont_connect=False):
        self.__variables = variables
        self.__connection = None
        self.__channel = None
        self.__dont_connect = dont_connect
        self.__couldnt_connect = 0
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
            log.info('Connecting to the Rabbit')
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
            self.__couldnt_connect = 0

        except pika.exceptions.ConnectionClosed as e1:
            log.error(str(type(e1)))
            log.warn('Could not connect to RabbitMQ. Connection will be attempted a few times when messages are sent.')
            self.__couldnt_connect = self.__couldnt_connect+1
            self.__connection = None

        except pika.exceptions.ProbableAuthenticationError as e2:
            log.error(str(type(e2)))
            log.warn('Could not connect to RabbitMQ. Connection will be attempted a few times when messages are sent.')
            self.__couldnt_connect = self.__couldnt_connect+1
            self.__connection = None

        except pika.exceptions.AMQPConnectionError as e3:
            log.error(str(type(e3)))
            log.warn('Could not connect to RabbitMQ. Connection will be attempted a few times when messages are sent.')
            self.__couldnt_connect = self.__couldnt_connect+1
            self.__connection = None

        except Exception as e4:
            log.error(str(type(e4)))
            if getattr(e4, '__module__', None) == pika.__name__:
                log.warn('Could not connect to RabbitMQ. Connection will be attempted a few times when messages are sent.')
                self.__couldnt_connect = self.__couldnt_connect+1
                self.__connection = None

    '''
    Send a log message to the RabbitMQ queue, unless
    the dont-connect parameter is set. In that case,
    the messages get logged into the normal log files.
    If the connection is dead, reconnection is attempted.
    '''
    def log_json_to_queue(self, dictionary_message, app_name, exchange, routing_key):
        body = json.dumps(dictionary_message)

        max_reconnect = 3
        if self.__dont_connect or self.__couldnt_connect > max_reconnect:
            log.info('RABBIT LOG MESSAGE (%s, %s, %s): %s' % (app_name, exchange, routing_key, body))
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
                    routing_key=routing_key,
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
        log.info('Creating new channel.')
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
>>>>>>> Stashed changes
