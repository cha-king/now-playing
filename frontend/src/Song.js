import styles from './Song.module.css';

function Song(props) {
    return (
        <div className={styles.song}>
            <img src={props.imageUrl} alt="album cover"/>
            <div>{props.title}</div>
            <div>{props.artist}</div>
            <div>{props.album}</div>
        </div>
    )
}

export default Song;
