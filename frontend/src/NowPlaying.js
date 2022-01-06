import { useState, useEffect, useRef } from 'react';

import styles from './NowPlaying.module.css';

const defaultTheme = {primary: '#FFFFFF', secondary: '#000000'};

function NowPlaying() {
    const [song, setSong] = useState(null);
    const [theme, setTheme] = useState(defaultTheme);
    const imgRef = useRef(null);
    
    useEffect(() => {
        async function getNowPlaying() {
            const response = await fetch('/api/now-playing');

            let song;
            let theme;
            if (response.status === 204) {
                song = null;
                theme = defaultTheme;
            } else {
                const data = await response.json();
                song = data.song;
                theme = data.theme;
            }
            setSong(song);
            setTheme(theme);
        }
        getNowPlaying();
    }, []);

    useEffect(() => {
        document.body.style.backgroundColor = theme.primary;
        document.body.style.color = theme.secondary;
        if (imgRef.current) {
            imgRef.current.style.border = `solid ${theme.secondary}`;
        }
    }, [theme]);

    useEffect(() => {
        function connect() {
            // TODO: Find workaround for CRA proxy not working for WS on Chrome
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
            const url = `${protocol}//${window.location.host}/api/ws/now-playing`;
            // const url = 'ws://localhost:8000/api/ws/now-playing';
            const ws = new WebSocket(url);
            ws.onmessage = function(event) {
                if (event.data) {
                    const data = JSON.parse(event.data);
                    setSong(data.song);
                    setTheme(data.theme);
                } else {
                    setSong(null);
                    setTheme(defaultTheme);
                }
            };
            ws.onclose = function(event) {
                const delay = 1000 + Math.random() * 1000;
                setTimeout(connect, delay)
            };
        }
        connect();
    }, []);

    if (song === null) {
        return (
            <div className={styles.empty}>
                <div>
                    <p>Nothing is currently playing..</p>
                    <p>Check back later!</p>
                </div>
            </div>
        )
    }
    
    // return (<Song title={song.name} artist={song.artist} album={song.album} imageUrl={song.image_url}/>)
    return (
        <div className={styles['now-playing']}>
            <img ref={imgRef} src={song.album.artwork_href} alt={song.album.name}/>
            <ul>
                <li className={styles['song-name']}>
                    <a href={song.href} target="_blank" rel="noreferrer">
                        {song.name}
                    </a>
                </li>
                <li className={styles['album-name']}>
                    <a href={song.album.href} target="_blank" rel="noreferrer">
                        {song.album.name}
                    </a>
                </li>
                <li className={styles['artist-name']}>
                    <a href={song.artist.href} target="_blank" rel="noreferrer">
                        {song.artist.name}
                    </a>
                </li>
            </ul>
        </div>
    )
}

export default NowPlaying;
