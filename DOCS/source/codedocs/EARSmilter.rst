.. EARS Milter Code Documentation - Main Milter class

EARS Milter main class/functions
################################

.. automodule:: EARSmilter

* :ref:`EARSlog`
* :ref:`milter`
* :ref:`ProcessMessage`
* :ref:`FileSys`

.. _EARSlog:

EARSlog
*******

.. autoclass:: EARSlog


.. _milter:

milter
******

.. autoclass:: milter(Milter.Base)
  
   .. automethod:: __init__
  
   .. py:function:: @Milter.noreply
      connect(IPname, family, hostaddr)
        
      Initializes when a new connection to the Milter is made via SMTP

   .. py:function:: @Milter.noreply
      header(name, hval)
      
      Processes headers from the incoming message and writes them to a variable for database storage
   
      .. code-block:: py
      
         rgxSubject = re.compile( '^(subject)', re.IGNORECASE | re.DOTALL )
         rgxMessageID = re.compile( '^(message-id)', re.IGNORECASE | re.DOTALL )
         
      Regular Expression searches used to extract and log the Subject and Message ID of incoming messages
        

   .. automethod:: eom
   
.. _ProcessMessage:
   
ProcessMessage
**************

.. autoclass:: ProcessMessage
   :members:
   :special-members:


.. _FileSys:
   
FileSys
*******

.. autoclass:: FileSys
   :members:
   :special-members:
