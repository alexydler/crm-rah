import * as oidc from "openid-client";
import { appOrigin } from "./session";

let configuration: Promise<oidc.Configuration> | undefined;
export function getOidcConfiguration(): Promise<oidc.Configuration> {
  if (configuration) return configuration;
  configuration = (async () => {
    if (!process.env.OIDC_ISSUER || !process.env.OIDC_CLIENT_ID) throw new Error("Configura OIDC_ISSUER y OIDC_CLIENT_ID");
    const issuer = new URL(process.env.OIDC_ISSUER);
    const local = ["localhost", "127.0.0.1", "[::1]"];
    const allowHttp = process.env.OIDC_ALLOW_INSECURE_LOCALHOST === "true" && local.includes(issuer.hostname) && local.includes(new URL(appOrigin()).hostname);
    const checkUrl = (url: URL) => {
      if (url.username || url.password || url.origin !== issuer.origin || (url.protocol !== "https:" && !(url.protocol === "http:" && allowHttp))) throw new Error("Endpoint OIDC no permitido");
    };
    checkUrl(issuer);
    const execute = [oidc.enableNonRepudiationChecks];
    if (allowHttp) execute.push(oidc.allowInsecureRequests);
    const config = await oidc.discovery(issuer, process.env.OIDC_CLIENT_ID, undefined,
      oidc.None(), {
        execute,
        [oidc.customFetch]: (input, options) => {
          checkUrl(new URL(input));
          const body = options.body instanceof Uint8Array ? new Uint8Array(options.body).buffer : options.body;
          return fetch(input, { ...options, body, redirect: "error", cache: "no-store", signal: AbortSignal.timeout(10000) });
        },
      });
    const metadata = config.serverMetadata();
    for (const endpoint of [metadata.authorization_endpoint, metadata.token_endpoint, metadata.jwks_uri]) {
      if (!endpoint) throw new Error("Discovery OIDC incompleto");
      checkUrl(new URL(endpoint));
    }
    return config;
  })();
  configuration.catch(() => { configuration = undefined; });
  return configuration;
}
export const callbackUrl = () => new URL("/auth/callback", appOrigin());
