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
                credentials=credentials,
                heartbeat_interval=variables.get('heartbeat_interval')
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
