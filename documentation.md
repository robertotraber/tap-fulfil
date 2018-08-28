Use this as a guide or a template for your tap's documentation. **Remove a section if it's not applicable.**

---

# Fulfil.IO

## Connecting Fulfil

### Requirements

To set up Fulfil in Stitch, you need:

_subdomain:_
-  **Subdomain**. This is the subdomain of your fulfil account.

_api_key:_
-  **API Key**. A version 1 API Key.

### Setup

You should already have a Fulfil.IO account before you can setup Stitch.

You will also need a personal API key available on your user page from settings.

The permissions of the integration will be the permissions on your account.

---

## Fulfil Replication

The data replication is incremental. For this a combination of `create_date`,
`write_date` and `id` of the record are used.

This reduces API usage and only new records are pushed to the data warehouse.

### Warning

The strategy could change in future where master records (products, customers)
are always pushed while transactional records (orders, invoices, journal entries)
are only pushed incrementally.

---

## Fulfil Table Schemas

### Contacts

- Table name: Contacts
- Description: Contacts including customers and suppliers.
- Primary key column(s): id
- Replicated fully or incrementally _(uses a bookmark to maintain state)_: FULL_TABLE
- Link to API endpoint documentation: https://api.fulfil.io/#tag/party.party

### Sales Orders 

- Table name: Sale Order
- Description: Sales Orders.
- Primary key column(s): id
- Replicated fully or incrementally _(uses a bookmark to maintain state)_: INCREMENTAL
- Bookmark column(s): create_date, write_date, id
- Link to API endpoint documentation: https://api.fulfil.io/#tag/sale.sale

---

## Troubleshooting / Other Important Info

* All timestamps are in UTC
