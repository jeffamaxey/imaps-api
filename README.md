# iMaps API

[![Build Status](https://travis-ci.org/goodwright/imaps-api.svg?branch=master)](https://travis-ci.org/goodwright/imaps-api.svg?branch=master)
[![Coverage Status](https://coveralls.io/repos/github/goodwright/imaps-api/badge.svg?branch=master)](https://coveralls.io/github/goodwright/imaps-api?branch=master)

This is the source code for the iMaps backend, responsible for authenticating users, providing access to data subject to permissions, and accepting jobs. It is accessible via a GraphQL API.

## Authorisation

The `signup` mutation is used to create a user account, and the `login` mutation is used to login. Both of these mutations have an `accessToken` property. This is a JSON Web Token (JWT) which should be supplied as a header with all requests that are on behalf of a signed in user:

```HTTP
Authorization: Bearer xxxxxxx...
```

Both of these mutations will also set a HTTP-only cookie on the client containing a refresh token, valid for one year.

Access tokens however are valid for fiteen minutes, after which time the server will reject them. You can obtain another token by either using the `login` mutation again, or by using the `accessToken` query. The latter will only return an access token if the query is accomapnied by a valid refresh token cookie.

Access tokens are how a client identifies itself to the server and last fifteen minutes once generated. Refresh tokens are how a client can obtain a new access token without username/password, and are valid for one year.
