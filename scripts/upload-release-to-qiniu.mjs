import { createReadStream, statSync } from "node:fs";
import path from "node:path";
import qiniu from "qiniu";

const [filePath] = process.argv.slice(2);
const accessKey = process.env.QINIU_ACCESS_KEY?.trim();
const secretKey = process.env.QINIU_SECRET_KEY?.trim();
const bucket = process.env.QINIU_BUCKET?.trim();
const tag = process.env.RELEASE_TAG?.trim();

if (!filePath || !accessKey || !secretKey || !bucket || !tag) {
  throw new Error("Usage: RELEASE_TAG=v0.1.0 node scripts/upload-release-to-qiniu.mjs <zip>");
}

const fileName = path.basename(filePath);
const keys = [
  `plugins/agent-case-share-skill/latest/${fileName}`,
  `plugins/agent-case-share-skill/${tag}/${fileName}`,
];

const mac = new qiniu.auth.digest.Mac(accessKey, secretKey);
const config = new qiniu.conf.Config();
const uploader = new qiniu.form_up.FormUploader(config);
const extra = new qiniu.form_up.PutExtra();
extra.mimeType = "application/zip";

function upload(key) {
  const token = new qiniu.rs.PutPolicy({ scope: `${bucket}:${key}` }).uploadToken(mac);

  return new Promise((resolve, reject) => {
    uploader.putStream(token, key, createReadStream(filePath), extra, (error, body, info) => {
      if (error) {
        reject(error);
        return;
      }

      if (info.statusCode >= 200 && info.statusCode < 300) {
        resolve(body);
        return;
      }

      reject(new Error(`Qiniu upload failed for ${key}: ${info.statusCode}`));
    });
  });
}

console.log(`Uploading ${fileName} (${statSync(filePath).size} bytes)`);
for (const key of keys) {
  await upload(key);
  console.log(`Uploaded ${key}`);
}

