# api.crystalprism.io
I started programming in January 2017 and am learning Python for back-end server development. api.crystalprism.io is the API for my website, [Crystal Prism](https://crystalprism.io). The API allows for the storage and retrieval of game scores, user-created drawings and thought posts, as well as user accounts. For user security, I implemented a JWT authentication flow from scratch that includes generating and verifying secure user tokens. To handle race conditions when writing to files, I implemented file locking operations with [`fcntl.flock`](https://docs.python.org/3.6/library/fcntl.html#fcntl.flock).

## Setup
To create your own copy of the Crystal Prism API, first clone this repository on your server. Next, install requirements by running `pip install -r requirements.txt`. Set up the API's necessary environment variables of "SECRET_KEY" for the salt used to generate the signature portion of the JWT for user authentication (set this as a secret key that only you know; it is imperative to keep this private for user account protection) and "ENV_TYPE" for the environment status (set this to "Dev" for testing or "Prod" for live), and start the server by running `flask run` (if you are making changes while the server is running, enter `flask run --reload` instead for instant updates).

## API Status
To check if the API is online, a client can send a request to the following endpoint.

**GET** /api/ping
* Retrieve a success message if the server is online. No bearer token is needed in the request Authorization header.
* Example response body:
```javascript
Success
```

## CanvaShare API
#### March 2017 - Present
[CanvaShare](https://crystalprism.io/canvashare/index.html) is a community drawing gallery that lets users create drawings and post them to a public gallery. Each user has a folder on the server for their drawings, as well as a folder for the drawing's attributes (title, number of likes, number of views, list of liked users). Drawings are stored as PNG files with numeric file names (*1.png*, *2.png*, etc.), and drawing information files are stored as JSON files with the same numeric file names (*1.json*, *2.json*, etc.).

**POST** /api/canvashare/drawing
* Post a drawing by sending the jsonified drawing data URI in base64 format and drawing title in the request body. Note that there must be a verified bearer token in the request Authorization header.
* Example request body:
```javascript
{
    "drawing": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAZ...",
    "title": "Welcome"
}
```

**GET** /api/canvashare/drawing/[artist]/[drawing_file]
* Retrieve an artist's drawing PNG file by specifying the artist's username and the drawing file name (e.g., *1.png*) in the request URL. No bearer token is needed in the request Authorization header.
* Example response body:<br />
![Welcome](canvashare/drawings/UUID/1.png)

**PATCH** /api/canvashare/drawing-info/[artist]/[drawing_id]
* Update a drawing's attributes by specifying the artist's username and the drawing file name without the extension (e.g., *1*) in the request URL. Send the jsonified attribute request ("like", "unlike", "view") in the request body. Note that there must be a verified bearer token in the request Authorization header.
* Example response body:
```javascript
{
    "request": "view"
}
```

**GET** /api/canvashare/drawing-info/[artist]/[drawing_id]
* Retrieve an artist's drawing's attributes by specifying the artist's username and the drawing file name without the extension (e.g., *1*) in the request URL. No bearer token is needed in the request Authorization header.
* Example response body:
```javascript
{
    "liked_users": [
      "esther"
    ],
    "likes": 1,
    "timestamp": "2017-10-05T00:00:00.000000+00:00",
    "title": "Welcome",
    "views": 0
}
```

**GET** /api/canvashare/gallery?start=[request_start]&end=[request_end]
* Retrieve all users' drawing file paths in the format "[artist]/[drawing_id].png", in order of newest to oldest drawings. Optionally specify the number of drawings via the request URL's start and end query parameters. No bearer token is needed in the request Authorization header.
* Example response body:
```javascript
{
    [
      "user/3.png",
      "esther/12.png",
      "esther/11.png",
      "esther/10.png",
      "user/2.png",
      "esther/9.png",
      "esther/8.png",
      "esther/7.png",
      "esther/6.png",
      "esther/5.png",
      "user/1.png"
    ]
}
```

**GET** /api/canvashare/gallery/[artist]?start=[request_start]&end=[request_end]
* Retrieve all of a single user's drawing file paths in the format "[artist]/[drawing_name].png", in order of newest to oldest drawings, by specifying the artist's username in the request URL. Optionally specify the number of drawings via the request URL's start and end query parameters. No bearer token is needed in the request Authorization header.
* Example response body:
```javascript
{
    [
      "esther/14.png",
      "esther/13.png",
      "esther/12.png",
      "esther/11.png",
      "esther/10.png",
      "esther/9.png",
      "esther/8.png",
      "esther/7.png",
      "esther/6.png",
      "esther/5.png",
      "esther/4.png"
    ]
}
```

## Rhythm of Life API
#### July 2017 - Present
[Rhythm of Life](https://crystalprism.io/rhythm-of-life/index.html) is an educational take on the classic game Snake, involving moving a heart to avoid stressors and seek relievers to maintain a healthy blood pressure.

**POST** /api/rhythm-of-life
* Post a score by sending the jsonified score and lifespan in the request body. Note that there must be a verified bearer token in the request Authorization header.
* Example request body:
```javascript
{
    "lifespan": "00:01:31",
    "score": 91
}
```

**GET** /api/rhythm-of-life?start=[request_start]&end=[request_end]
* Retrieve all users' game scores, in order of highest to lowest score. Optionally specify the number of scores via the request URL's start and end query parameters. No bearer token is needed in the request Authorization header.
* Example response body:
```javascript
[
    {
      "lifespan": "00:01:31",
      "player": "esther",
      "score": 91,
      "timestamp": "2017-10-27T04:00:51.679625+00:00"
    },
    {
      "lifespan": "00:00:23",
      "player": "esther",
      "score": 23,
      "timestamp": "2017-10-27T03:54:50.802001+00:00"
    },
    {
      "lifespan": "00:00:17",
      "player": "esther",
      "score": 17,
      "timestamp": "2017-10-27T03:53:31.190392+00:00"
    },
    {
      "lifespan": "00:00:09",
      "player": "esther",
      "score": 9,
      "timestamp": "2017-10-27T03:55:04.910504+00:00"
    },
    {
      "lifespan": "00:00:08",
      "player": "esther",
      "score": 8,
      "timestamp": "2017-10-27T03:55:14.748859+00:00"
    }
]
```

## Thought Writer API
#### August 2017 - Present
[Thought Writer](https://crystalprism.io/thought-writer/index.html) is a community post board for users to post short ideas for others to read and comment on.

**POST** /api/thought-writer/post
* Post a thought post by sending the jsonified post content, title, and public status ("true" or "false") in the request body. Note that there must be a verified bearer token in the request Authorization header.
* Example request body:
```javascript
{
    "content": "I find inspiration in the colors outside.",
    "public": false,
    "title": "The Beauty of Design"
}
```

**PATCH** /api/thought-writer/post
* Update a thought post by sending the jsonified post content, post creation timestamp (UTC), title, and public status (*true* or *false*) in the request body. Note that there must be a verified bearer token in the request Authorization header.
* Example request body:
```javascript
{
    "content": "I often find inspiration in the color combinations found in nature.",
    "public": true,
    "timestamp": "2017-11-05T02:21:35.017651+00:00",
    "title": "The Beauty of Design"
}
```

**DELETE** /api/thought-writer/post
* Delete a thought post by sending the jsonified post creation timestamp (UTC) in the request body. Note that there must be a verified bearer token in the request Authorization header.
* Example request body:
```javascript
{
    "timestamp": "2017-11-05T02:21:35.017651+00:00"
}
```

**GET** /api/thought-writer/post/[writer_name]/[post_timestamp]
* Retrieve a user's thought post by specifying the writer's username and the thought post's URI-encoded creation timestamp (UTC) in the request URL. Note that there must be a verified bearer token in the request Authorization header for a private post to be retrieved.
* Example response body:
```javascript
{
    "comments": [
      {
        "commenter": "esther",
        "content": "Thanks for welcoming me!",
        "timestamp": "2017-11-05T02:50:01.392277+00:00"
      }
    ],
    "content": "Welcome to Thought Writer, a community post board for you to write your ideas for the world to see. You can also create your own private posts or comment on others' posts. Click the yellow paper icon to get started!",
    "timestamp": "2017-10-05T00:00:00.000000+00:00",
    "title": "Welcome",
    "writer": "user"
}
```

**POST** /api/thought-writer/comment/[writer_name]/[post_timestamp]
* Post a comment to a thought post by specifying the post writer's username and the thought post's URI-encoded creation timestamp (UTC) in the request URL, as well as the jsonified comment content in the request body. Note that there must be a verified bearer token in the request Authorization header.
* Example request body:
```javascript
{
    "content": "I really like this post."
}
```

**PATCH** /api/thought-writer/comment/[writer_name]/[post_timestamp]
* Update a comment to a thought post by specifying the post writer's username and the thought post's URI-encoded creation timestamp (UTC) in the request URL, as well as the jsonified comment content and original comment creation timestamp (UTC) in the request body. Note that there must be a verified bearer token in the request Authorization header.
* Example request body:
```javascript
{
    "content": "I really like this post. Great writing!",
    "timestamp": "2017-11-05T02:47:21.744277+00:00"
}
```

**DELETE** /api/thought-writer/comment/[writer_name]/[post_timestamp]
* Delete a comment to a thought post by specifying the post writer's username and the thought post's URI-encoded creation timestamp (UTC) in the request URL, as well as the jsonified comment creation timestamp (UTC) in the request body. Note that there must be a verified bearer token in the request Authorization header.
* Example request body:
```javascript
{
    "timestamp": "2017-11-05T02:47:21.744277+00:00"
}
```

**GET** /api/thought-writer/post-board?start=[request_start]&end=[request_end]
* Retrieve all users' public thought posts. Optionally specify the number of thought posts via the request URL's start and end query parameters. No bearer token is needed in the request Authorization header.
* Example response body:
```javascript
[
    {
      "comments": [],
      "content": "<font color=\"#00c6fc\"><b>Only when you find yourself can you understand the world and your place within it. To deny oneself would be to have a limited view of the world, as you yourself are part of it not only in perception but in external interfacing and influence.</b></font>",
      "timestamp": "2017-10-27T04:31:07.730128+00:00",
      "title": "Finding yourself",
      "writer": "esther"
    },
    {
      "comments": [
        {
          "commenter": "esther",
          "content": "Thanks for welcoming me!",
          "timestamp": "2017-11-05T02:50:01.392277+00:00"
        }
      ],
      "content": "Welcome to Thought Writer, a community post board for you to write your ideas for the world to see. You can also create your own private posts or comment on others' posts. Click the yellow paper icon to get started!",
      "timestamp": "2017-10-05T00:00:00.000000+00:00",
      "title": "Welcome",
      "writer": "user"
    }
]
```

**GET** /api/thought-writer/post-board/[writer_name]?start=[request_start]&end=[request_end]
* Retrieve all of a single user's thought posts by specifying the writer's username in the request URL. Optionally specify the number of thought posts via the request URL's start and end query parameters. If there is a verified bearer token for the writer in the request Authorization header, the server will send the user's private and public posts; otherwise, only the public posts will be sent.
* Example response body:
```javascript
{
    "comments": [],
    "content": "<font color=\"#00c6fc\"><b>Only when you find yourself can you understand the world and your place within it. To deny oneself would be to have a limited view of the world, as you yourself are part of it not only in perception but in external interfacing and influence.</b></font>",
    "public": true,
    "timestamp": "2017-10-27T04:31:07.730128+00:00",
    "title": "Finding yourself"
}
```

## Shapes in Rain API
#### September 2017 - Present
[Shapes in Rain](https://crystalprism.io/shapes-in-rain/index.html) is a game in which random shapes appear periodically on the page for a user to clear with a click.

**POST** /api/shapes-in-rain
* Post a score by sending the jsonified score in the request body. Note that there must be a verified bearer token in the request Authorization header.
* Example request body:
```javascript
{
    "score": 10
}
```

**GET** /api/shapes-in-rain?start=[request_start]&end=[request_end]
* Retrieve all users' game scores, in order of highest to lowest score. Optionally specify the number of scores via the request URL's start and end query parameters. No bearer token is needed in the request Authorization header.
* Example response body:
```javascript
[
    {
      "player": "esther",
      "score": 10,
      "timestamp": "2017-10-26T18:06:10.330929+00:00"
    },
    {
      "player": "esther",
      "score": 8,
      "timestamp": "2017-10-27T03:11:02.955038+00:00"
    }
]
```

## User Account API
#### September 2017 - Present
Users who want to join the Crystal Prism community can create an account to store their Shapes in Rain and Rhythm of Life scores, their CanvaShare drawings, and their Thought Writer posts.

**POST** /api/user
* Create a user account by sending the jsonified username and password in the request body.
* Example request body:
```javascript
{
    "password": "password"
    "username": "username",
}
```

**GET** /api/user
* Retrieve a user's complete account information. Note that there must be a verified bearer token for the user in the request Authorization header.
* Example response body:
```javascript
{
    "about": "", // User-entered blurb that appears on public profile
    "admin": false, // Admin status
    "background_color": "#ffffff", // User-chosen background color of public profile
    "comment_count": 0, // Number of user's Thought Writer comments on posts
    "drawing_count": 1, // Number of CanvaShare drawings created
    "email": "", // User-entered on My Account page
    "email_public": false, // User specifies if email is viewable on public profile
    "first_name": "", // User-entered on My Account page
    "icon_color": "#000000", // User-chosen icon color of public profile
    "last_name": "", // User-entered on My Account page
    "liked_drawings": [], // "[artist]/[drawing_id]" for each of user's liked drawings
    "member_id": "UUID", // Random universally unique identifier
    "member_since": "2017-10-04T00:00:00.000000+00:00", // UTC timestamp of when user created account
    "name_public": false, // User specifies if name is viewable on public profile
    "password": "$2b$12$GD0XvyXV/8i9G1...", // Password hashed with bcrypt algorithm
    "post_count": 1, // Number of user's Thought Writer posts
    "rhythm_high_lifespan": "00:00:00", // High lifespan in Rhythm of Life
    "rhythm_high_score": 0, // High score in Rhythm of Life (lifespan converted to integer)
    "rhythm_plays": 0, // Number of Rhythm of Life game plays
    "rhythm_scores": [], // Array of user's Rhythm of Life scores that includes timestamp
    "shapes_high_score": 0, // High score in Shapes in Rain
    "shapes_plays": 0, // Number of Shapes in Rain game plays
    "shapes_scores": [], // Array of user's Shapes in Rain scores that includes timestamp
    "status": "active", // Can be active or deleted
    "username": "user" // Case-sensitive username
}
```

**PATCH** /api/user
* Update a user's account information by specifying the jsonified account updates in the request body. Note that there must be a verified bearer token for the user in the request Authorization header.
* Example request body:
```javascript
{
    "about": "Founder of Crystal Prism",
    "background_color": "#9fffad",
    "email": "",
    "email_public": false,
    "first_name": "",
    "icon_color": "#ffb4e6",
    "last_name": "",
    "password": "",
    "name_public": false,
    "username": "esther"
}
```

**DELETE** /api/user
* Delete a user's account. No request body is needed. Note that there must be a verified bearer token for the user in the request Authorization header.

**GET** /api/user/[username]
* Retrieve a user's limited account information. No bearer token is needed in the request Authorization header.
* Example response body:
```javascript
{
    "about": "",
    "background_color": "#ffffff",
    "comment_count": 0,
    "drawing_count": 1,
    "email": "",
    "icon_color": "#000000",
    "member_since": "2017-10-04T00:00:00.000000+00:00",
    "name": "",
    "post_count": 0,
    "rhythm_high_lifespan": "00:00:00",
    "shapes_high_score": 0,
    "username": "user"
}
```

**GET** /api/user/verify
* Check if a bearer token in a request Authorization header is valid and receive the expiration time (in seconds since epoch) if so.
* Example response body:
```javascript
{
    "username": "esther",
    "exp": 1509855369
}
```

**GET** /api/users?start=[request_start]&end=[request_end]
* Retrieve all users' usernames. Optionally specify the number of users via the request URL's start and end query parameters. Note that there must be a verified bearer token in the request Authorization header.
* Example response body:
```javascript
[
    "esther",
    "user"
]
```

**GET** /api/login
* Check if a username and password in a request Authorization header match the username and password stored for a user account and receive a [JSON Web Token](https://jwt.io/) if so. The JWT is set to expire after 1 hour.
* Example response body:
```javascript
{
    "token": "eyJhbGciOiAiSFMyNTYiLCAidHlwIjogIkpXVC..."
}
```
