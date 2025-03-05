NMDC API Utilities Usage Notes
=================================

Welcome to NMDC API Utilities usage notes. Here you will find helpful information on how to use the tools provided by this package.

Filtering should be formatted in MongoDB query syntax. The function build_filter in the DataProcessing class can be used to help build filters. Additonally, there are available functions in the CollectionSearch class that can be used to filter data without having to pass in a specific filter.
The CollectionSearch class is a foundational component that defines common behaviors and properties between collections. Each subclass is designed to be more user-friendly and specific for certain collections, making them the recommended entry points for using the package. Each function of CollectionSearch can be accessed via each subclass.
The subclasses will prefill necessary information for the user, such as the collection name. This will allow the user to focus on the data they are interested in, rather than the specifics of the collection.
