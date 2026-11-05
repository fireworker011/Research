'use strict';

async function api(url, { method = 'GET', body } = {}) {
  const token = process.env.GITHUB_TOKEN;
  if (!token) throw new Error('missing GITHUB_TOKEN');
  const res = await fetch(url, {
    method,
    headers: {
      Authorization: `Bearer ${token}`,
      Accept: 'application/vnd.github+json',
      'X-GitHub-Api-Version': '2022-11-28',
      'User-Agent': 'cw-engine'
    },
    body: body ? JSON.stringify(body) : undefined
  });
  const text = await res.text();
  let json = null;
  try {
    json = text ? JSON.parse(text) : null;
  } catch {
    json = { raw: text };
  }
  if (!res.ok) {
    const err = new Error(`github ${res.status} ${url}`);
    err.status = res.status;
    throw err;
  }
  return json;
}

function repoApi(p) {
  const repo = process.env.GITHUB_REPOSITORY;
  if (!repo) throw new Error('missing GITHUB_REPOSITORY');
  return `https://api.github.com/repos/${repo}${p}`;
}

async function findIssueByTitle(title) {
  for (let page = 1; page <= 10; page++) {
    const issues = await api(repoApi(`/issues?state=all&per_page=100&page=${page}`));
    if (!Array.isArray(issues) || !issues.length) return null;
    const hit = issues.find((i) => i.title === title && !i.pull_request);
    if (hit) return hit;
    if (issues.length < 100) return null;
  }
  return null;
}

async function ensureIssue(title, body) {
  const hit = await findIssueByTitle(title);
  if (hit) {
    if (hit.state === 'closed') {
      await api(repoApi(`/issues/${hit.number}`), { method: 'PATCH', body: { state: 'open' } });
      hit.state = 'open';
    }
    return { issue: hit, created: false };
  }
  const issue = await api(repoApi('/issues'), { method: 'POST', body: { title, body } });
  return { issue, created: true };
}

async function postComment(issueNumber, body) {
  return api(repoApi(`/issues/${issueNumber}/comments`), { method: 'POST', body: { body } });
}

module.exports = { api, repoApi, findIssueByTitle, ensureIssue, postComment };
