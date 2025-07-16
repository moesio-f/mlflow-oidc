import qs from "querystring";

// Base URLs
const MLFLOW_URL = rstrip(process.env.MLFLOW_TRACKING_SERVER_URL, "/");
const AUTH_URL = rstrip(process.env.KEYCLOAK_UMA_URL, "/");

// OIDC configuration
const CLIENT_ID = process.env.OIDC_CLIENT_ID;
const CLIENT_SECRET = process.env.OIDC_CLIENT_SECRET;

/*
 * Handle a request for a MLFlow
 * tracking server.
 *
 * @param r - original request;
 * */
async function handle(r) {
  // Check if contains authorization header
  if (!r.headersIn.hasOwnProperty("Authorization")) {
    r.return(400, "Missing authorization header.");
    return;
  }

  // Check if user represented by token is allowed
  let decision = await is_allowed(r);
  if (decision["result"]) {
    await run_mlflow(r);
  } else {
    r.return(403, JSON.stringify(decision));
  }
}

/*
 * Check whether a user is allowed
 * to access the given resource.
 *
 * @param r - original request.
 * */
async function is_allowed(r) {
  let allowed = await ngx.fetch(AUTH_URL, {
    body: toURLSearchParams({
      grant_type: "urn:ietf:params:oauth:grant-type:uma-ticket",
      audience: CLIENT_ID,
      permission_resource_format: "uri",
      permission_resource_matching_uri: "True",
      response_mode: "decision",
      permission: r.uri,
    }),
    headers: new Headers({
      Authorization: r.headersIn["Authorization"],
      "Content-Type": "application/x-www-form-urlencoded",
      "User-Agent": "nginx-intercept-js",
    }),
    method: "POST",
    verify: false,
  });
  let decision = await allowed.json();
  return decision;
}

/*
 * Run MLFlow from client request.
 *
 * @param r - original request.
 * */
async function run_mlflow(r) {
  // Construct equivalent MLFlow URL
  let url = `${MLFLOW_URL}/${lstrip(r.uri, "/")}`;
  if (Object.keys(r.args).length > 0) {
    url = `${url}?${qs.stringify(r.args)}`;
  }

  // Call the MLFlow API
  let reply = await ngx.fetch(url, {
    body: r.requestText,
    headers: new Headers({
      "Content-Type": r.headersIn["Content-Type"],
      "User-Agent": r.headersIn["User-Agent"],
    }),
    method: r.method,
    verify: false,
  });

  // Get response
  let data = await reply.text();

  // Update output headers
  for (let key in reply.headers) {
    if (reply.headers.hasOwnProperty(key)) {
      r.headersOut[key] = reply.headers[key];
    }
  }

  r.return(reply.status, data);
}

/*
 * Right strip a string for a given char.
 *
 * @param str - string;
 * @param ch - character to remove.
 * */
function rstrip(str, ch) {
  if (str.endsWith(ch)) {
    return str.slice(0, -1);
  }
  return str;
}

/*
 * Left strip a string for a given char.
 *
 * @param str - string.
 * @param ch - character to remove.
 * */
function lstrip(str, ch) {
  if (str.startsWith(ch)) {
    return str.slice(1);
  }
  return str;
}

/*
 * Convert an object to URL
 * encoded params.
 *
 * @param obj - object.
 * */
function toURLSearchParams(obj) {
  let parts = [];
  for (let key in obj) {
    if (obj.hasOwnProperty(key)) {
      parts.push(`${key}=${obj[key]}`);
    }
  }
  return parts.join("&");
}

export default { handle };

