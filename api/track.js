// Счётчик посетителей и загрузок SCU.
//
// Как работает «честный» подсчёт: для каждого запроса считается
// SHA256(соль + IP + User-Agent) — сам IP нигде не хранится.
// По этому хешу в Vercel Blob создаётся ровно один маркер
// (scu-stats/visits/<hash> или scu-stats/downloads/<hash>), поэтому
// один и тот же пользователь не может увеличить счётчик повторно:
// счётчик — это просто количество маркеров, а не сумма кликов.
//
// Требуется подключённый Blob Store в Vercel (Storage → Create → Blob),
// тогда переменная BLOB_READ_WRITE_TOKEN подставится автоматически.
// TRACK_SALT — необязательная соль; после её смены счётчики начнутся
// заново (старые маркеры останутся в сторадже).
const crypto = require('crypto');
const { head, put, list } = require('@vercel/blob');

const PREFIX_VISIT = 'scu-stats/visits/';
const PREFIX_DOWNLOAD = 'scu-stats/downloads/';
const SALT = process.env.TRACK_SALT || 'scu-track-salt-v1';

function userHash(req) {
    const ip = String(req.headers['x-forwarded-for'] || '').split(',')[0].trim()
        || String(req.headers['x-real-ip'] || '');
    const ua = String(req.headers['user-agent'] || '');
    return crypto.createHash('sha256').update(SALT + '|' + ip + '|' + ua).digest('hex');
}

async function markUser(prefix, hash) {
    const path = prefix + hash;
    try {
        await head(path);
        return; // уже считали этого пользователя
    } catch (e) {
        // маркера нет — создаём; повторная запись того же пути идемпотентна
    }
    await put(path, String(Date.now()), { access: 'public', addRandomSuffix: false });
}

async function countPrefix(prefix) {
    let count = 0;
    let cursor;
    do {
        const page = await list({ prefix, cursor, limit: 1000 });
        count += page.blobs.length;
        cursor = page.hasMore ? page.cursor : undefined;
    } while (cursor);
    return count;
}

module.exports = async (req, res) => {
    try {
        const type = req.query.type === 'download' ? 'download' : 'visit';
        const hash = userHash(req);
        await markUser(type === 'visit' ? PREFIX_VISIT : PREFIX_DOWNLOAD, hash);

        const [visits, downloads] = await Promise.all([
            countPrefix(PREFIX_VISIT),
            countPrefix(PREFIX_DOWNLOAD),
        ]);
        res.setHeader('Cache-Control', 'no-store');
        res.status(200).json({ visits, downloads });
    } catch (e) {
        res.status(500).json({ error: 'track_failed' });
    }
};
