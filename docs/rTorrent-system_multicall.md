### Introduction

The syntax for using system.multicall to speed up the query of multiple variables.

!!! info
    I've picked up this document from [gi-torrent wiki](https://code.google.com/p/gi-torrent).
    Copyright &copy; Hans.Hasert@gmail.com


***
### Details

The way to combine multiple queries is to use the `system.multicall` and specify which methods we want to call.
The XML would look something like this:

```xml
<?xml version="1.0"?>
<methodCall>
<methodName />  // "system.multicall"
 <params>
  <param>
   <value>
    <array>
     <data>
      <value>
       <struct>
        <member>
         <name />  // "methodName"
         <value><string /></value>  // the 1st actual method to be called
        </member>
        <member>
         <name />  // "params"
         <value>
          <array>
           <data>
            <value><string /></value>  // list of parameters
           </data>
          </array>
         </value>
        </member>
       </struct>
      </value>
      <value>
       <struct>
        <member>
         <name />  // "methodName"
         <value><string /></value>  // the 2nd actual method to be called
        </member>
        <member>
         <name />  // "params"
         <value>
          <array>
           <data>
            <value><string /></value>  // list of parameters
           </data>
          </array>
         </value>
        </member>
       </struct>
      </value>
     </data>
    </array>
   </value>
  </param>
 </params>
</methodCall>
```

This will invoke multiple xmlrpc methods to be called, the response looks like this:


```xml
<?xml version="1.0" encoding="UTF-8"?>
<methodResponse>
 <params>
  <param>
   <value>
    <array>
     <data>
      <value>
       <array>
        <data>
         <value><i8>123245</i8></value>
        </data>
       </array>
      </value>
      <value>
       <array>
        <data>
         <value><i8>12345</i8></value>
        </data>
       </array>
      </value>
     </data>
    </array>
   </value>
  </param>
 </params>
</methodResponse>
```
