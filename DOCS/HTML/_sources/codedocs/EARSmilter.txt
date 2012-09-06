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

.. autoclass:: EARSmilter.EARSmilter.EARSlog


.. _milter:

milter
******

.. autoclass:: EARSmilter.EARSmilter.milter(Milter.Base)
   :members:
   
  
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
        


   
.. _ProcessMessage:
   
ProcessMessage
**************

.. autoclass:: EARSmilter.EARSmilter.ProcessMessage
   :members:
   :special-members:


.. _FileSys:
   
FileSys
*******

.. autoclass:: EARSmilter.EARSmilter.FileSys
   :members:
   :special-members:
